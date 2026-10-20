"""
In-memory Customer Facing Display State Manager.
Allows real-time synchronization between the POS Station (Guard Laptop)
and the Customer-Facing Secondary Screen (Smartphone / Tablet).
"""

import time
from typing import Any

from backend.config import VIETQR_ACCOUNT_NAME, VIETQR_ACCOUNT_NO, VIETQR_BANK_ID
from backend.vietqr_service import build_vietqr_url

_STATE: dict[str, Any] = {
    "state": "IDLE",  # "IDLE", "CHECKOUT", "SUCCESS"
    "lane_name": "CỔNG 2 — TRẠM RA KHU C (2 LÀN) & KHU B",
    "plate_number": None,
    "user_type": "STUDENT",
    "fee": 5000,
    "overnight_surcharge": 0,
    "qr_url": None,
    "card_id": None,
    "ticket_id": None,
    "updated_at": time.time(),
}


def get_customer_display_state() -> dict[str, Any]:
    global _STATE
    # Auto-reset from SUCCESS to IDLE after 8 seconds
    if _STATE.get("state") == "SUCCESS":
        elapsed = time.time() - _STATE.get("updated_at", 0)
        if elapsed > 8.0:
            _STATE["state"] = "IDLE"
            _STATE["plate_number"] = None
            _STATE["user_type"] = "STUDENT"
            _STATE["qr_url"] = None
            _STATE["updated_at"] = time.time()
    return dict(_STATE)


def set_customer_display_state(new_state: dict[str, Any]) -> dict[str, Any]:
    global _STATE
    _STATE.update(new_state)
    _STATE["updated_at"] = time.time()
    return dict(_STATE)


def trigger_checkout_display(
    plate_number: str,
    fee: int = 5000,
    overnight_surcharge: int = 0,
    card_id: str | None = None,
    ticket_id: str | None = None,
    qr_url: str | None = None,
    lane_name: str = "CỔNG 2 — TRẠM RA KHU C (2 LÀN) & KHU B",
    user_type: str = "STUDENT",
) -> dict[str, Any]:
    """Trigger customer display to show the payment VietQR code."""
    final_qr = qr_url
    if not final_qr:
        memo = f"GUIXE {card_id or ticket_id or 'UTH'}".strip()
        final_qr = build_vietqr_url(
            amount=fee,
            add_info=memo,
            bank_id=VIETQR_BANK_ID,
            account_no=VIETQR_ACCOUNT_NO,
            account_name=VIETQR_ACCOUNT_NAME,
        )

    return set_customer_display_state({
        "state": "CHECKOUT",
        "lane_name": lane_name,
        "plate_number": plate_number,
        "fee": fee,
        "overnight_surcharge": overnight_surcharge,
        "card_id": card_id,
        "ticket_id": ticket_id,
        "qr_url": final_qr,
        "user_type": user_type,
    })


def trigger_success_display(plate_number: str, amount: int = 5000, user_type: str = "STUDENT") -> dict[str, Any]:
    """Trigger customer display to show success checkmark and barrier lift."""
    return set_customer_display_state({
        "state": "SUCCESS",
        "plate_number": plate_number,
        "fee": amount,
        "user_type": user_type,
        "qr_url": None,
    })


def trigger_idle_display(lane_name: str | None = None) -> dict[str, Any]:
    """Reset customer display back to idle welcome mode."""
    state_update = {
        "state": "IDLE",
        "plate_number": None,
        "user_type": "STUDENT",
        "fee": 5000,
        "overnight_surcharge": 0,
        "qr_url": None,
        "card_id": None,
        "ticket_id": None,
    }
    if lane_name:
        state_update["lane_name"] = lane_name
    return set_customer_display_state(state_update)
