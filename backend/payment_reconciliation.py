"""
Payment Reconciliation & Automated Barrier Control Module.
Reconciles bank credit transactions (from MBBank API / Webhooks) with parking tickets.
Automatically confirms payment, marks ticket as PAID/COMPLETED, and opens the exit barrier.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any

from backend.config import DB_PATH, DEFAULT_PARKING_FEE
from backend.db import (
    _connect,
    append_audit_log,
    append_parking_event,
    fetch_active_ticket_by_card_id,
    fetch_ticket_detail,
    update_zone_occupancy,
)
from integrations.barrier_service import barrier_simulator

logger = logging.getLogger(__name__)


def extract_parking_reference(description: str) -> dict[str, str | None]:
    """Extract card_id or ticket_id from bank transfer description / memo.

    Examples:
        - "GUIXE CARD_001" -> card_id: "CARD_001"
        - "GUIXE T20261020163012ABCD" -> ticket_id: "T20261020163012ABCD"
        - "GUIXE CARD-UTH-123" -> card_id: "CARD-UTH-123"
        - "CARD_001 THANH TOAN" -> card_id: "CARD_001"
    """
    clean = (description or "").strip().upper()

    # Match Ticket ID pattern: T followed by 14 digits and 4 chars
    ticket_match = re.search(r"\b(T\d{14}[A-Z0-9]{4})\b", clean)
    if ticket_match:
        return {"ticket_id": ticket_match.group(1), "card_id": None}

    # Match GUIXE <REF>
    guixe_match = re.search(r"GUIXE[\s_:-]+([A-Z0-9_-]+)", clean)
    if guixe_match:
        ref = guixe_match.group(1).strip()
        if ref.startswith("T") and len(ref) >= 15:
            return {"ticket_id": ref, "card_id": None}
        return {"ticket_id": None, "card_id": ref}

    # Match CARD_<REF> or RFID_<REF>
    card_match = re.search(r"\b((?:CARD|RFID)[A-Z0-9_-]*)\b", clean)
    if card_match:
        return {"ticket_id": None, "card_id": card_match.group(1).strip()}

    return {"ticket_id": None, "card_id": None}


def record_bank_transaction(
    transaction_id: str,
    amount: int,
    description: str,
    account_no: str | None = None,
    transaction_time: str | None = None,
    ticket_id: str | None = None,
    card_id: str | None = None,
    reconciled: bool = False,
    raw_payload: dict | None = None,
    db_path=None,
) -> bool:
    """Save incoming bank transaction record for auditing and idempotency check."""
    target_db = db_path if db_path is not None else DB_PATH
    raw_json = json.dumps(raw_payload, ensure_ascii=False) if raw_payload else None
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trans_time = transaction_time or now_str

    with _connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO bank_transactions(
                transaction_id, account_no, amount, description, transaction_time,
                ticket_id, card_id, reconciled, reconciled_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                account_no,
                int(amount),
                description,
                trans_time,
                ticket_id,
                card_id,
                1 if reconciled else 0,
                now_str if reconciled else None,
                raw_json,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def is_bank_transaction_processed(transaction_id: str, db_path=None) -> bool:
    """Check if bank transaction_id was already processed."""
    target_db = db_path if db_path is not None else DB_PATH
    clean_id = (transaction_id or "").strip()
    if not clean_id:
        return False
    with _connect(target_db) as conn:
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT reconciled FROM bank_transactions WHERE transaction_id = ? AND reconciled = 1",
            (clean_id,),
        ).fetchone()
        return row is not None


def reconcile_bank_transaction(
    payload: dict[str, Any],
    db_path=None,
) -> dict[str, Any]:
    """Process incoming bank transaction, verify ticket fee, mark as PAID, and open barrier."""
    target_db = db_path if db_path is not None else DB_PATH

    transaction_id = str(payload.get("transaction_id") or payload.get("id") or payload.get("refNo") or "").strip()
    if not transaction_id:
        transaction_id = f"MB_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    # Idempotency check: don't process duplicate transaction
    if is_bank_transaction_processed(transaction_id, db_path=target_db):
        return {
            "success": True,
            "reconciled": True,
            "already_processed": True,
            "transaction_id": transaction_id,
            "message": f"Transaction {transaction_id} already processed",
        }

    try:
        amount = int(float(payload.get("amount") or payload.get("change") or payload.get("creditAmount") or 0))
    except (ValueError, TypeError):
        amount = 0

    description = str(payload.get("description") or payload.get("remark") or "").strip()
    account_no = str(payload.get("accountNo") or payload.get("account_no") or "").strip()
    trans_time = str(payload.get("transactionDate") or payload.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()

    # Extract Card ID or Ticket ID from memo
    refs = extract_parking_reference(description)
    card_id = refs.get("card_id")
    ticket_id = refs.get("ticket_id")

    ticket = None
    if card_id:
        ticket = fetch_active_ticket_by_card_id(card_id, db_path=target_db)
    elif ticket_id:
        ticket = fetch_ticket_detail(ticket_id, db_path=target_db)

    # Fallback search if description contains only partial card or plate
    if ticket is None and card_id:
        with _connect(target_db) as conn:
            conn.row_factory = __import__("sqlite3").Row
            row = conn.execute(
                "SELECT * FROM parking_logs WHERE card_id = ? AND status IN ('IN_PARKING', 'NEEDS_REVIEW') ORDER BY entry_time DESC LIMIT 1",
                (card_id,),
            ).fetchone()
            if row:
                ticket = dict(row)

    if ticket is None:
        # Save unmatched transaction for audit
        record_bank_transaction(
            transaction_id=transaction_id,
            amount=amount,
            description=description,
            account_no=account_no,
            transaction_time=trans_time,
            ticket_id=ticket_id,
            card_id=card_id,
            reconciled=False,
            raw_payload=payload,
            db_path=target_db,
        )
        return {
            "success": True,
            "reconciled": False,
            "transaction_id": transaction_id,
            "amount": amount,
            "message": "Transaction recorded but no active parking ticket matched the transfer description.",
        }

    # Match verified: check fee amount
    matched_ticket_id = ticket["ticket_id"]
    required_fee = int(ticket.get("fee") or DEFAULT_PARKING_FEE)
    zone_assigned = ticket.get("zone_assigned")
    lane_exit = ticket.get("lane_exit") or "LANE_EXIT_GATE2"
    effective_card = card_id or ticket.get("card_id")

    if amount < required_fee:
        record_bank_transaction(
            transaction_id=transaction_id,
            amount=amount,
            description=description,
            account_no=account_no,
            transaction_time=trans_time,
            ticket_id=matched_ticket_id,
            card_id=effective_card,
            reconciled=False,
            raw_payload=payload,
            db_path=target_db,
        )
        return {
            "success": False,
            "reconciled": False,
            "transaction_id": transaction_id,
            "ticket_id": matched_ticket_id,
            "amount_paid": amount,
            "required_fee": required_fee,
            "message": f"Underpaid: received {amount:,.0f} VND, required {required_fee:,.0f} VND",
        }

    # Update ticket payment status to PAID and COMPLETED
    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE parking_logs
            SET payment_status = 'PAID',
                payment_method = 'VIETQR',
                paid_at = ?,
                status = 'COMPLETED',
                exit_time = COALESCE(exit_time, ?)
            WHERE ticket_id = ?
            """,
            (now_ts, now_ts, matched_ticket_id),
        )
        conn.commit()

    # Decrement zone occupancy if checkout completed
    if zone_assigned:
        try:
            update_zone_occupancy(zone_assigned, delta=-1, db_path=target_db)
        except Exception as exc:
            logger.warning("Failed to decrement zone occupancy on auto-reconcile: %s", exc)

    # Open the Barrier automatically!
    barrier_command = barrier_simulator.open_barrier(
        lane_id=lane_exit,
        reason=f"auto-reconciled-vietqr-paid-{amount}",
        actor_username="system-mbbank-reconcile",
    )

    # Record reconciled bank transaction
    record_bank_transaction(
        transaction_id=transaction_id,
        amount=amount,
        description=description,
        account_no=account_no,
        transaction_time=trans_time,
        ticket_id=matched_ticket_id,
        card_id=effective_card,
        reconciled=True,
        raw_payload=payload,
        db_path=target_db,
    )

    # Append parking event and audit log
    try:
        append_parking_event(
            ticket_id=matched_ticket_id,
            event_type="PAYMENT_CONFIRMED",
            actor_username="system-mbbank",
            actor_role="system",
            plate_text=ticket.get("plate_entry"),
            details={
                "amount": amount,
                "payment_method": "VIETQR",
                "transaction_id": transaction_id,
                "barrier_opened": True,
            },
            db_path=target_db,
        )
        append_audit_log(
            actor_username="system-mbbank",
            actor_role="system",
            action="payment.auto_reconcile",
            target_type="ticket",
            target_id=matched_ticket_id,
            details_json=json.dumps({"amount": amount, "transaction_id": transaction_id, "card_id": effective_card}, ensure_ascii=False),
            db_path=target_db,
        )
    except Exception as exc:
        logger.warning("Failed to record audit/events for payment: %s", exc)

    return {
        "success": True,
        "reconciled": True,
        "transaction_id": transaction_id,
        "ticket_id": matched_ticket_id,
        "card_id": effective_card,
        "plate_entry": ticket.get("plate_entry"),
        "amount_paid": amount,
        "fee": required_fee,
        "payment_status": "PAID",
        "ticket_status": "COMPLETED",
        "barrier_command": barrier_command.__dict__,
        "message": f"Payment of {amount:,.0f} VND confirmed for ticket {matched_ticket_id}. Barrier opened automatically.",
    }
