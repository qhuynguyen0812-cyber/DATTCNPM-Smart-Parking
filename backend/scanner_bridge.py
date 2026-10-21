"""
Wireless Mobile Scanner Bridge.
Allows a smartphone (via Web NFC / Camera) to act as a wireless RFID reader
and transmit scanned card IDs in real-time to the main POS desktop station.
"""

import time
from typing import Any

_SCANNER_STATE: dict[str, Any] = {
    "card_id": None,
    "plate_text": None,
    "user_type": "STUDENT",
    "mode": "entry",
    "timestamp": 0.0,
}


def push_scan_event(
    card_id: str,
    plate_text: str | None = None,
    user_type: str = "STUDENT",
    mode: str = "entry",
) -> dict[str, Any]:
    global _SCANNER_STATE
    clean_card = (card_id or "").strip()
    clean_plate = (plate_text or "").strip() or None
    _SCANNER_STATE = {
        "card_id": clean_card,
        "plate_text": clean_plate,
        "user_type": user_type or "STUDENT",
        "mode": mode or "entry",
        "timestamp": time.time(),
    }
    return dict(_SCANNER_STATE)


def get_latest_scan(since: float = 0.0) -> dict[str, Any] | None:
    if _SCANNER_STATE["timestamp"] > since and _SCANNER_STATE["card_id"]:
        return dict(_SCANNER_STATE)
    return None
