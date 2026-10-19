import sqlite3
from datetime import datetime
from typing import Any
from uuid import uuid4

from backend.config import DB_PATH
from backend.plate_format import format_vn_plate, normalize_plate_text


ACTIVE_STATUS = "IN_PARKING"
COMPLETED_STATUS = "COMPLETED"
PENDING_MATCH = "PENDING"
MATCH = "MATCH"
MISMATCH = "MISMATCH"


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


def vehicle_entry(plate_text: str, image_path: str | None = None, detected_path: str | None = None, plate_path: str | None = None, ocr_confidence: float | None = None) -> dict[str, Any]:
    clean_plate = _sanitize_plate_text(plate_text)
    if not _normalized_plate_text(clean_plate):
        return {"success": False, "message": "Invalid plate text", "plate_entry": clean_plate}

    ticket_id = create_ticket_id()
    entry_time = _utc_like_timestamp()
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO parking_logs (
                ticket_id, plate_entry, plate_exit, entry_time, exit_time, status, match_result,
                entry_image_path, entry_detected_path, entry_plate_path, exit_image_path, exit_detected_path, exit_plate_path,
                ocr_confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id, clean_plate, None, entry_time, None, ACTIVE_STATUS, PENDING_MATCH,
                image_path, detected_path, plate_path, None, None, None, _safe_confidence(ocr_confidence),
            ),
        )
    return {"success": True, "ticket_id": ticket_id, "plate_entry": clean_plate, "entry_time": entry_time, "status": ACTIVE_STATUS}


def vehicle_exit(ticket_id: str, plate_text: str, image_path: str | None = None, detected_path: str | None = None, plate_path: str | None = None, ocr_confidence: float | None = None) -> dict[str, Any]:
    clean_ticket_id = (ticket_id or "").strip()
    if not clean_ticket_id:
        return {"success": False, "message": "Ticket ID is required"}

    clean_plate = _sanitize_plate_text(plate_text)
    if not _normalized_plate_text(clean_plate):
        return {"success": False, "message": "Invalid plate text", "plate_exit": clean_plate}

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ticket_id, plate_entry, status FROM parking_logs WHERE ticket_id = ?", (clean_ticket_id,))
        row = cursor.fetchone()
        if row is None:
            return {"success": False, "message": "Ticket ID not found"}

        _, plate_entry, status = row
        if status == COMPLETED_STATUS:
            return {"success": False, "message": "Vehicle already checked out"}

        exit_time = _utc_like_timestamp()
        match_result = MATCH if _normalized_plate_text(plate_entry) == _normalized_plate_text(clean_plate) else MISMATCH
        cursor.execute(
            """
            UPDATE parking_logs
            SET plate_exit = ?, exit_time = ?, status = ?, match_result = ?,
                exit_image_path = ?, exit_detected_path = ?, exit_plate_path = ?, ocr_confidence = ?
            WHERE ticket_id = ?
            """,
            (clean_plate, exit_time, COMPLETED_STATUS, match_result, image_path, detected_path, plate_path, _safe_confidence(ocr_confidence), clean_ticket_id),
        )

    return {
        "success": True,
        "ticket_id": clean_ticket_id,
        "plate_entry": plate_entry,
        "plate_exit": clean_plate,
        "exit_time": exit_time,
        "match_result": match_result,
    }

