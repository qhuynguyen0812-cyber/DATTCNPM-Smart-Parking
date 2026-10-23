import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import uuid4

from backend.config import (
    DB_PATH,
    DEFAULT_PARKING_FEE,
    OVERNIGHT_CUTOFF_HOUR,
    OVERNIGHT_SURCHARGE,
)
from backend.db import (
    append_audit_log,
    append_parking_event,
    fetch_active_ticket_by_card_id,
    update_zone_occupancy,
)
from backend.plate_format import format_vn_plate, normalize_plate_text
from backend.vietqr_service import build_parking_vietqr

logger = logging.getLogger(__name__)


ACTIVE_STATUS = "IN_PARKING"
COMPLETED_STATUS = "COMPLETED"
NEEDS_REVIEW_STATUS = "NEEDS_REVIEW"
CANCELLED_STATUS = "CANCELLED"
PENDING_MATCH = "PENDING"
MATCH = "MATCH"
MISMATCH = "MISMATCH"
REVIEW_RESOLVED_MATCH = "RESOLVED_MATCH"
REVIEW_RESOLVED_APPROVED = "RESOLVED_APPROVED"
REVIEW_RESOLVED_REJECTED = "RESOLVED_REJECTED"
BLOCKING_ACTIVE_STATUSES = {ACTIVE_STATUS, NEEDS_REVIEW_STATUS}
FINAL_STATUSES = {COMPLETED_STATUS, CANCELLED_STATUS}
LOW_CONFIDENCE_THRESHOLD = 0.55


def create_ticket_id() -> str:
    return f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid4())[:4].upper()}"


def _utc_like_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sanitize_plate_text(plate_text: str | None) -> str:
    return format_vn_plate(plate_text or "")


def _normalized_plate_text(plate_text: str | None) -> str:
    return normalize_plate_text(plate_text or "")


def _safe_confidence(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric < 0:
        return 0.0
    if numeric > 1:
        return 1.0
    return numeric


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


@contextmanager
def _write_transaction():
    """Serialized read-check-write transaction.

    BEGIN IMMEDIATE acquires the write lock up front so that concurrent
    ticket operations cannot both pass a duplicate-status check.
    """
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _actor_name(actor: Any | None) -> str | None:
    if actor is None:
        return None
    if isinstance(actor, str):
        return actor.strip() or None
    return getattr(actor, "username", None)


def _actor_role(actor: Any | None) -> str | None:
    if actor is None or isinstance(actor, str):
        return None
    return getattr(actor, "role", None)


def _safe_event(ticket_id: str | None, event_type: str, **kwargs):
    try:
        append_parking_event(ticket_id, event_type, db_path=DB_PATH, **kwargs)
    except Exception as exc:
        logger.warning("append_parking_event failed for %s: %s", event_type, exc)


def _safe_audit(actor_username: str | None, actor_role: str | None, action: str, **kwargs):
    try:
        append_audit_log(actor_username, actor_role, action, db_path=DB_PATH, **kwargs)
    except Exception as exc:
        logger.warning("append_audit_log failed for %s: %s", action, exc)


def _json_details(**details) -> str:
    return json.dumps({k: v for k, v in details.items() if v is not None}, ensure_ascii=False)


def _review_reason(confidence: float | None, manual_override: bool, mismatch: bool = False, ocr_review_required: bool = False) -> str | None:
    reasons: list[str] = []
    if mismatch:
        reasons.append("PLATE_MISMATCH")
    if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD and not manual_override:
        reasons.append("LOW_OCR_CONFIDENCE")
    if ocr_review_required and not manual_override:
        reasons.append("OCR_REVIEW_REQUIRED")
    return ";".join(reasons) or None


def calculate_parking_fee(entry_time_str: str, exit_time_str: str | None = None, is_staff: bool = False) -> dict[str, Any]:
    """Calculate base fee and overnight surcharge (past 23h cutoff or next-day checkout).

    Cán bộ - Giảng viên - CNV (is_staff=True) are 100% exempt from parking fees (0 VNĐ).
    """
    if is_staff:
        return {
            "base_fee": 0,
            "overnight_surcharge": 0,
            "total_fee": 0,
            "is_overnight": False,
            "is_staff": True,
        }

    base_fee = DEFAULT_PARKING_FEE
    overnight_surcharge = 0
    fmt = "%Y-%m-%d %H:%M:%S"

    try:
        dt_entry = datetime.strptime((entry_time_str or "").strip(), fmt)
    except Exception:
        dt_entry = datetime.now()

    if exit_time_str:
        try:
            dt_exit = datetime.strptime(exit_time_str.strip(), fmt)
        except Exception:
            dt_exit = datetime.now()
    else:
        dt_exit = datetime.now()

    is_overnight = False
    if dt_exit.date() > dt_entry.date():
        is_overnight = True
    elif dt_exit.hour >= OVERNIGHT_CUTOFF_HOUR and dt_entry.hour < OVERNIGHT_CUTOFF_HOUR:
        is_overnight = True

    if is_overnight:
        overnight_surcharge = OVERNIGHT_SURCHARGE

    total_fee = base_fee + overnight_surcharge
    return {
        "base_fee": base_fee,
        "overnight_surcharge": overnight_surcharge,
        "total_fee": total_fee,
        "is_overnight": is_overnight,
        "is_staff": False,
    }


def normalize_gate_name(gate: str | None) -> str:
    """Normalize user-friendly gate strings to standard identifiers."""
    if not gate:
        return ""
    g = gate.strip().upper().replace(" ", "_").replace("-", "_")
    if any(k in g for k in ("GATE_E", "CONG_E", "CỔNG_E", "KHU_E")) or g == "E":
        return "GATE_E"
    if any(k in g for k in ("GATE_A", "CONG_A", "CỔNG_A", "GATE_1", "CONG_1", "CỔNG_1", "VO_OANH", "VÕ_OANH")) or g in ("A", "1"):
        return "GATE_A"
    if any(k in g for k in ("GATE_B", "CONG_B", "CỔNG_B")) or g == "B":
        return "GATE_B"
    if any(k in g for k in ("GATE_C", "CONG_C", "CỔNG_C", "GATE_2", "CONG_2")) or g in ("C", "2"):
        return "GATE_C"
    return g


def validate_gate_routing(user_type: str, gate: str | None, is_entry: bool = True) -> tuple[bool, str, str]:
    """UTH Campus 1 Gate Routing Rules:

    - Giảng viên / Cán bộ (STAFF): Chỉ đi vào và ra qua Cổng E (Nhà xe Khu E).
    - Sinh viên (STUDENT): Chỉ được vào mỗi Cổng A. Còn lại cổng nào ra cũng được.
    """
    clean_user = (user_type or "STUDENT").strip().upper()
    norm_gate = normalize_gate_name(gate)

    if is_entry:
        if clean_user == "STAFF":
            if not norm_gate or norm_gate in ("GATE_E", "GATE_4"):
                return True, "GATE_E", ""
            return False, norm_gate, "Giảng viên / Cán bộ chỉ được đi vào qua Cổng E (Nhà xe Khu E)!"
        else:  # STUDENT or GUEST
            if not norm_gate or norm_gate in ("GATE_A", "GATE_1"):
                return True, "GATE_A", ""
            if norm_gate == "GATE_E":
                return False, norm_gate, "Sinh viên chỉ được vào gửi xe qua Cổng A (Võ Oanh)! Vui lòng di chuyển sang Cổng A."
            return True, norm_gate, ""
    else:  # Exit
        if clean_user == "STAFF":
            if not norm_gate or norm_gate in ("GATE_E", "GATE_4"):
                return True, "GATE_E", ""
            return False, norm_gate, "Giảng viên / Cán bộ chỉ được đi ra qua Cổng E!"
        else:  # STUDENT can exit through ANY gate
            if not norm_gate:
                norm_gate = "GATE_A"
            return True, norm_gate, ""


def vehicle_entry(
    plate_text: str,
    image_path: str | None = None,
    detected_path: str | None = None,
    plate_path: str | None = None,
    ocr_confidence: float | None = None,
    ocr_engine: str | None = None,
    ocr_text: str | None = None,
    manual_override: bool = False,
    ocr_review_required: bool = False,
    actor: Any | None = None,
    card_id: str | None = None,
    gate_entry: str | None = None,
    lane_entry: str | None = "LANE_1",
    zone_assigned: str | None = None,
    user_type: str = "STUDENT",
) -> dict[str, Any]:
    clean_plate = _sanitize_plate_text(plate_text)
    normalized_plate = _normalized_plate_text(clean_plate)
    if not normalized_plate:
        return {"success": False, "message": "Invalid plate text", "plate_entry": clean_plate}

    clean_card_id = (card_id or "").strip() or None
    clean_user_type = (user_type or "STUDENT").strip().upper()
    if clean_card_id:
        try:
            from backend.card_service import get_card
            registered_card = get_card(clean_card_id, db_path=DB_PATH)
            if registered_card and registered_card.get("user_type"):
                if user_type in (None, "", "STUDENT") and registered_card["user_type"] == "STAFF":
                    clean_user_type = "STAFF"
        except Exception as _card_ex:
            logger.debug("Failed to lookup card registry: %s", _card_ex)

    valid_gate, effective_gate_entry, gate_err = validate_gate_routing(clean_user_type, gate_entry, is_entry=True)
    if not valid_gate:
        return {"success": False, "message": gate_err, "plate_entry": clean_plate, "user_type": clean_user_type}
    gate_entry = effective_gate_entry

    is_staff = clean_user_type == "STAFF"
    if not zone_assigned:
        from backend.db import suggest_optimal_zone
        zone_assigned = "ZONE_E" if is_staff else suggest_optimal_zone("STUDENT", db_path=DB_PATH)

    entry_fee = 0 if is_staff else DEFAULT_PARKING_FEE
    entry_payment_status = "PAID" if is_staff else "UNPAID"
    entry_payment_method = "FREE" if is_staff else None

    confidence = _safe_confidence(ocr_confidence)
    review_reason = _review_reason(confidence, manual_override, ocr_review_required=ocr_review_required)
    review_required = bool(review_reason)

    with _write_transaction() as conn:
        cursor = conn.cursor()

        # Check if card_id is already in use by an active ticket
        if clean_card_id:
            cursor.execute(
                "SELECT ticket_id, plate_entry FROM parking_logs WHERE card_id = ? AND status IN (?, ?)",
                (clean_card_id, ACTIVE_STATUS, NEEDS_REVIEW_STATUS),
            )
            card_row = cursor.fetchone()
            if card_row is not None:
                return {
                    "success": False,
                    "message": f"Card ID {clean_card_id} is already in use by active ticket {card_row[0]}",
                    "ticket_id": card_row[0],
                    "plate_entry": card_row[1],
                    "card_id": clean_card_id,
                }

        placeholders = ", ".join(["?"] * len(BLOCKING_ACTIVE_STATUSES))
        cursor.execute(
            f"SELECT ticket_id, plate_entry, entry_time, status FROM parking_logs WHERE status IN ({placeholders}) ORDER BY entry_time DESC",
            tuple(BLOCKING_ACTIVE_STATUSES),
        )
        existing = None
        for active_ticket_id, active_plate_entry, active_entry_time, status in cursor.fetchall():
            if _normalized_plate_text(active_plate_entry) == normalized_plate:
                existing = (active_ticket_id, active_entry_time, status)
                break
        if existing is not None:
            return {
                "success": False,
                "message": "Vehicle already has an active ticket",
                "ticket_id": existing[0],
                "plate_entry": clean_plate,
                "entry_time": existing[1],
                "status": existing[2],
            }

        ticket_id = create_ticket_id()
        entry_time = _utc_like_timestamp()
        existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(parking_logs)").fetchall()}
        required_columns = {
            "review_required": "INTEGER NOT NULL DEFAULT 0",
            "review_reason": "TEXT",
            "resolved_by": "TEXT",
            "resolved_at": "TEXT",
            "resolution_note": "TEXT",
            "cancel_reason": "TEXT",
            "entry_actor": "TEXT",
            "exit_actor": "TEXT",
            "card_id": "TEXT",
            "gate_entry": "TEXT",
            "lane_entry": "TEXT",
            "zone_assigned": "TEXT",
            "gate_exit": "TEXT",
            "lane_exit": "TEXT",
            "fee": "INTEGER NOT NULL DEFAULT 5000",
            "overnight_surcharge": "INTEGER NOT NULL DEFAULT 0",
            "payment_method": "TEXT",
            "payment_status": "TEXT",
            "paid_at": "TEXT",
            "user_type": "TEXT NOT NULL DEFAULT 'STUDENT'",
        }
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE parking_logs ADD COLUMN {column_name} {column_type}")
        existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(parking_logs)").fetchall()}
        insert_columns = [
            "ticket_id", "plate_entry", "plate_exit", "entry_time", "exit_time", "status", "match_result",
            "entry_image_path", "entry_detected_path", "entry_plate_path", "exit_image_path", "exit_detected_path", "exit_plate_path",
            "entry_ocr_confidence", "exit_ocr_confidence", "entry_ocr_engine", "exit_ocr_engine", "entry_ocr_text", "exit_ocr_text",
            "entry_manual_override", "exit_manual_override", "review_required", "review_reason", "entry_actor",
        ]
        insert_values = [
            ticket_id, clean_plate, None, entry_time, None, ACTIVE_STATUS, PENDING_MATCH,
            image_path, detected_path, plate_path, None, None, None,
            confidence, None, ocr_engine, None, (ocr_text or "").strip() or None, None,
            1 if manual_override else 0, 0, 1 if review_required else 0, review_reason, _actor_name(actor),
        ]

        if "user_type" in existing_columns:
            insert_columns.append("user_type")
            insert_values.append(clean_user_type)
        if "card_id" in existing_columns:
            insert_columns.append("card_id")
            insert_values.append(clean_card_id)
        if "gate_entry" in existing_columns:
            insert_columns.append("gate_entry")
            insert_values.append(gate_entry)
        if "lane_entry" in existing_columns:
            insert_columns.append("lane_entry")
            insert_values.append(lane_entry)
        if "zone_assigned" in existing_columns:
            insert_columns.append("zone_assigned")
            insert_values.append(zone_assigned)
        if "fee" in existing_columns:
            insert_columns.append("fee")
            insert_values.append(entry_fee)
        if "overnight_surcharge" in existing_columns:
            insert_columns.append("overnight_surcharge")
            insert_values.append(0)
        if "payment_status" in existing_columns:
            insert_columns.append("payment_status")
            insert_values.append(entry_payment_status)
        if "payment_method" in existing_columns:
            insert_columns.append("payment_method")
            insert_values.append(entry_payment_method)

        if "plate_number" in existing_columns and "plate_number" not in insert_columns:
            insert_columns.insert(1, "plate_number")
            insert_values.insert(1, clean_plate)
        if "time_in" in existing_columns and "time_in" not in insert_columns:
            time_index = insert_columns.index("entry_time")
            insert_columns.insert(time_index + 1, "time_in")
            insert_values.insert(time_index + 1, entry_time)

        placeholders = ", ".join(["?"] * len(insert_columns))
        columns_sql = ", ".join(insert_columns)
        cursor.execute(f"INSERT INTO parking_logs ({columns_sql}) VALUES ({placeholders})", tuple(insert_values))

    if zone_assigned:
        try:
            update_zone_occupancy(zone_assigned, delta=1, db_path=DB_PATH)
        except Exception as exc:
            logger.warning("Failed to increment occupancy for zone %s: %s", zone_assigned, exc)

    _safe_event(ticket_id, "VEHICLE_ENTRY", actor_username=_actor_name(actor), actor_role=_actor_role(actor), plate_text=clean_plate, confidence=confidence, source=ocr_engine or "manual", details={"manual_override": manual_override, "review_reason": review_reason, "card_id": clean_card_id, "zone": zone_assigned, "user_type": clean_user_type})
    _safe_audit(_actor_name(actor), _actor_role(actor), "vehicle.entry", target_type="ticket", target_id=ticket_id, details_json=_json_details(plate=clean_plate, card_id=clean_card_id, zone=zone_assigned, user_type=clean_user_type, review_reason=review_reason))
    return {
        "success": True,
        "ticket_id": ticket_id,
        "plate_entry": clean_plate,
        "entry_time": entry_time,
        "status": ACTIVE_STATUS,
        "review_required": review_required,
        "review_reason": review_reason,
        "card_id": clean_card_id,
        "gate_entry": gate_entry,
        "lane_entry": lane_entry,
        "zone_assigned": zone_assigned,
        "user_type": clean_user_type,
        "fee": entry_fee,
    }


def vehicle_exit(
    ticket_id: str | None = None,
    plate_text: str = "",
    image_path: str | None = None,
    detected_path: str | None = None,
    plate_path: str | None = None,
    ocr_confidence: float | None = None,
    ocr_engine: str | None = None,
    ocr_text: str | None = None,
    manual_override: bool = False,
    ocr_review_required: bool = False,
    actor: Any | None = None,
    card_id: str | None = None,
    gate_exit: str | None = None,
    lane_exit: str | None = None,
    payment_method: str = "CASH",
    payment_status: str = "PAID",
    user_type: str | None = None,
) -> dict[str, Any]:
    clean_ticket_id = (ticket_id or "").strip()
    clean_card_id = (card_id or "").strip()

    if not clean_ticket_id and clean_card_id:
        active_card_ticket = fetch_active_ticket_by_card_id(clean_card_id, db_path=DB_PATH)
        if active_card_ticket:
            clean_ticket_id = active_card_ticket["ticket_id"]
        else:
            return {"success": False, "message": f"No active ticket found for Card ID {clean_card_id}"}

    if not clean_ticket_id:
        return {"success": False, "message": "Ticket ID or Card ID is required"}

    clean_plate = _sanitize_plate_text(plate_text)
    if not _normalized_plate_text(clean_plate):
        return {"success": False, "message": "Invalid plate text", "plate_exit": clean_plate}

    confidence = _safe_confidence(ocr_confidence)
    with _write_transaction() as conn:
        cursor = conn.cursor()
        log_columns = {r[1] for r in cursor.execute("PRAGMA table_info(parking_logs)").fetchall()}
        user_type_expr = "user_type" if "user_type" in log_columns else "'STUDENT'"

        cursor.execute(
            f"SELECT ticket_id, plate_entry, status, review_required, entry_time, zone_assigned, card_id, {user_type_expr} FROM parking_logs WHERE ticket_id = ?",
            (clean_ticket_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return {"success": False, "message": "Ticket ID not found"}

        _, plate_entry, status, entry_review_required, entry_time, zone_assigned, stored_card_id, stored_user_type = row
        effective_card_id = clean_card_id or stored_card_id or ""
        effective_user_type = (user_type or stored_user_type or "STUDENT").strip().upper()
        is_staff = effective_user_type == "STAFF"

        valid_gate, effective_gate_exit, gate_err = validate_gate_routing(effective_user_type, gate_exit, is_entry=False)
        if not valid_gate:
            return {"success": False, "message": gate_err, "plate_exit": clean_plate, "user_type": effective_user_type}
        gate_exit = effective_gate_exit

        if status == COMPLETED_STATUS:
            return {"success": False, "message": "Vehicle already checked out"}
        if status == CANCELLED_STATUS:
            return {"success": False, "message": "Ticket is cancelled"}
        if status == NEEDS_REVIEW_STATUS:
            return {"success": False, "message": "Ticket requires review before checkout can continue"}

        exit_time = _utc_like_timestamp()
        is_match = _normalized_plate_text(plate_entry) == _normalized_plate_text(clean_plate)
        match_result = MATCH if is_match else MISMATCH
        review_reason = _review_reason(confidence, manual_override, mismatch=not is_match, ocr_review_required=(ocr_review_required or bool(entry_review_required)))
        review_required = bool(review_reason)
        new_status = NEEDS_REVIEW_STATUS if review_required else COMPLETED_STATUS

        # Calculate tariff and overnight surcharge (CB-GV-CNV is completely exempt)
        tariff = calculate_parking_fee(entry_time, exit_time, is_staff=is_staff)
        final_fee = tariff["total_fee"]
        overnight_surcharge = tariff["overnight_surcharge"]
        effective_payment_method = "FREE" if is_staff else payment_method
        effective_payment_status = "PAID" if is_staff else payment_status
        effective_paid_at = exit_time if (new_status == COMPLETED_STATUS and effective_payment_status == "PAID") else None

        update_user_type_sql = ", user_type = ?" if "user_type" in log_columns else ""
        update_params = [
            clean_plate, exit_time, new_status, match_result,
            image_path, detected_path, plate_path, confidence, ocr_engine,
            (ocr_text or "").strip() or None, 1 if manual_override else 0, 1 if review_required else 0, review_reason, _actor_name(actor),
            gate_exit, lane_exit, final_fee, overnight_surcharge, effective_payment_method, effective_payment_status,
            effective_paid_at,
        ]
        if "user_type" in log_columns:
            update_params.append(effective_user_type)
        update_params.extend([clean_ticket_id, ACTIVE_STATUS])

        cursor.execute(
            f"""
            UPDATE parking_logs
            SET plate_exit = ?, exit_time = ?, status = ?, match_result = ?,
                exit_image_path = ?, exit_detected_path = ?, exit_plate_path = ?, exit_ocr_confidence = ?, exit_ocr_engine = ?,
                exit_ocr_text = ?, exit_manual_override = ?, review_required = ?, review_reason = ?, exit_actor = ?,
                gate_exit = ?, lane_exit = ?, fee = ?, overnight_surcharge = ?, payment_method = ?, payment_status = ?,
                paid_at = ?{update_user_type_sql}
            WHERE ticket_id = ? AND status = ?
            """,
            tuple(update_params),
        )
        if cursor.rowcount == 0:
            return {"success": False, "message": "Vehicle already checked out"}

    # Update zone occupancy if checkout is completed
    if new_status == COMPLETED_STATUS and zone_assigned:
        try:
            update_zone_occupancy(zone_assigned, delta=-1, db_path=DB_PATH)
        except Exception as exc:
            logger.warning("Failed to decrement occupancy for zone %s: %s", zone_assigned, exc)

    # Barrier automatically lifts for staff (CB-GV-CNV) on exit
    if new_status == COMPLETED_STATUS and is_staff:
        try:
            from integrations.barrier_service import barrier_simulator
            barrier_simulator.open_barrier(lane_exit or "LANE_EXIT_1", reason="staff-free-exit")
        except Exception as exc:
            logger.warning("Failed to open barrier for staff exit: %s", exc)

    vietqr_payload = None
    if not is_staff and payment_method and payment_method.upper() == "VIETQR" and final_fee > 0:
        vietqr_payload = build_parking_vietqr(
            card_id=effective_card_id,
            amount=final_fee,
            ticket_id=clean_ticket_id,
        )

    _safe_event(clean_ticket_id, "VEHICLE_EXIT", actor_username=_actor_name(actor), actor_role=_actor_role(actor), plate_text=clean_plate, confidence=confidence, source=ocr_engine or "manual", details={"manual_override": manual_override, "match_result": match_result, "review_reason": review_reason, "fee": final_fee, "payment_method": effective_payment_method, "user_type": effective_user_type})
    _safe_audit(_actor_name(actor), _actor_role(actor), "vehicle.exit", target_type="ticket", target_id=clean_ticket_id, details_json=_json_details(plate_entry=plate_entry, plate_exit=clean_plate, match_result=match_result, status=new_status, fee=final_fee, user_type=effective_user_type))
    return {
        "success": True,
        "ticket_id": clean_ticket_id,
        "card_id": effective_card_id,
        "plate_entry": plate_entry,
        "plate_exit": clean_plate,
        "exit_time": exit_time,
        "match_result": match_result,
        "status": new_status,
        "review_required": review_required,
        "review_reason": review_reason,
        "fee": final_fee,
        "overnight_surcharge": overnight_surcharge,
        "payment_method": effective_payment_method,
        "payment_status": effective_payment_status,
        "user_type": effective_user_type,
        "gate_exit": gate_exit,
        "lane_exit": lane_exit,
        "zone_assigned": zone_assigned,
        "vietqr": vietqr_payload,
    }


def resolve_review_ticket(ticket_id: str, resolution: str, actor: Any | None = None, note: str | None = None) -> dict[str, Any]:
    clean_ticket_id = (ticket_id or "").strip()
    clean_resolution = (resolution or "").strip().upper()
    if clean_resolution not in {"APPROVE_EXIT", "REJECT_EXIT", "MARK_MATCH"}:
        return {"success": False, "message": "Invalid resolution"}

    new_status = COMPLETED_STATUS if clean_resolution in {"APPROVE_EXIT", "MARK_MATCH"} else NEEDS_REVIEW_STATUS
    match_result = REVIEW_RESOLVED_MATCH if clean_resolution == "MARK_MATCH" else (REVIEW_RESOLVED_APPROVED if clean_resolution == "APPROVE_EXIT" else REVIEW_RESOLVED_REJECTED)
    resolved_at = _utc_like_timestamp()
    zone_to_decrement = None

    with _write_transaction() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT status, zone_assigned FROM parking_logs WHERE ticket_id = ?", (clean_ticket_id,)).fetchone()
        if row is None:
            return {"success": False, "message": "Ticket ID not found"}
        if row[0] != NEEDS_REVIEW_STATUS:
            return {"success": False, "message": "Ticket does not require review"}
        zone_to_decrement = row[1]
        cursor.execute(
            """
            UPDATE parking_logs
            SET status = ?, match_result = ?, review_required = ?, resolved_by = ?, resolved_at = ?, resolution_note = ?
            WHERE ticket_id = ? AND status = ?
            """,
            (new_status, match_result, 0 if new_status == COMPLETED_STATUS else 1, _actor_name(actor), resolved_at, (note or "").strip() or None, clean_ticket_id, NEEDS_REVIEW_STATUS),
        )

    if new_status == COMPLETED_STATUS and zone_to_decrement:
        try:
            update_zone_occupancy(zone_to_decrement, delta=-1, db_path=DB_PATH)
        except Exception as exc:
            logger.warning("Failed to decrement occupancy on resolve for zone %s: %s", zone_to_decrement, exc)

    _safe_event(clean_ticket_id, "REVIEW_RESOLVED", actor_username=_actor_name(actor), actor_role=_actor_role(actor), details={"resolution": clean_resolution, "note": note})
    _safe_audit(_actor_name(actor), _actor_role(actor), "ticket.resolve", target_type="ticket", target_id=clean_ticket_id, details_json=_json_details(resolution=clean_resolution, note=note))
    return {"success": True, "ticket_id": clean_ticket_id, "status": new_status, "match_result": match_result, "resolved_at": resolved_at}


def cancel_ticket(ticket_id: str, actor: Any | None = None, reason: str | None = None) -> dict[str, Any]:
    clean_ticket_id = (ticket_id or "").strip()
    clean_reason = (reason or "").strip()
    if not clean_reason:
        return {"success": False, "message": "Cancel reason is required"}
    zone_to_decrement = None

    with _write_transaction() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT status, zone_assigned FROM parking_logs WHERE ticket_id = ?", (clean_ticket_id,)).fetchone()
        if row is None:
            return {"success": False, "message": "Ticket ID not found"}
        if row[0] in FINAL_STATUSES:
            return {"success": False, "message": "Finalized ticket cannot be cancelled"}
        zone_to_decrement = row[1]
        cursor.execute(
            "UPDATE parking_logs SET status = ?, cancel_reason = ?, review_required = 0 WHERE ticket_id = ?",
            (CANCELLED_STATUS, clean_reason, clean_ticket_id),
        )

    if zone_to_decrement:
        try:
            update_zone_occupancy(zone_to_decrement, delta=-1, db_path=DB_PATH)
        except Exception as exc:
            logger.warning("Failed to decrement occupancy on cancel for zone %s: %s", zone_to_decrement, exc)

    _safe_event(clean_ticket_id, "TICKET_CANCELLED", actor_username=_actor_name(actor), actor_role=_actor_role(actor), details={"reason": clean_reason})
    _safe_audit(_actor_name(actor), _actor_role(actor), "ticket.cancel", target_type="ticket", target_id=clean_ticket_id, details_json=_json_details(reason=clean_reason))
    return {"success": True, "ticket_id": clean_ticket_id, "status": CANCELLED_STATUS}


def get_ticket_detail(ticket_id: str) -> dict | None:
    from backend.db import fetch_ticket_detail

    return fetch_ticket_detail(ticket_id, db_path=DB_PATH)
