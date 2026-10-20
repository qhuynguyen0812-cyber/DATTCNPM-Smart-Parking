"""
VietQR & Napas 247 Payment Gateway Helper.
Generates dynamic VietQR payment links and QR payloads for UTH Smart Parking.
"""

import urllib.parse
from typing import Any

from backend.config import (
    VIETQR_ACCOUNT_NAME,
    VIETQR_ACCOUNT_NO,
    VIETQR_BANK_ID,
    VIETQR_TEMPLATE,
)


def build_vietqr_url(
    amount: int,
    add_info: str,
    bank_id: str | None = None,
    account_no: str | None = None,
    template: str | None = None,
    account_name: str | None = None,
) -> str:
    """Build dynamic VietQR quick link image URL based on Napas 247 standard."""
    target_bank = (bank_id or VIETQR_BANK_ID).strip()
    target_account = (account_no or VIETQR_ACCOUNT_NO).strip()
    target_template = (template or VIETQR_TEMPLATE).strip()
    target_name = (account_name or VIETQR_ACCOUNT_NAME).strip()

    base_url = f"https://img.vietqr.io/image/{target_bank}-{target_account}-{target_template}.png"
    params: dict[str, str] = {
        "amount": str(max(0, int(amount))),
        "addInfo": (add_info or "").strip(),
    }
    if target_name:
        params["accountName"] = target_name

    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"


def build_parking_vietqr(
    card_id: str,
    amount: int,
    ticket_id: str | None = None,
    bank_id: str | None = None,
    account_no: str | None = None,
    account_name: str | None = None,
) -> dict[str, Any]:
    """Generate standardized VietQR payment payload for a parking ticket."""
    clean_card = (card_id or "").strip()
    clean_ticket = (ticket_id or "").strip()
    target_bank = (bank_id or VIETQR_BANK_ID).strip()
    target_account = (account_no or VIETQR_ACCOUNT_NO).strip()
    target_name = (account_name or VIETQR_ACCOUNT_NAME).strip()

    # Memo format: GUIXE_<CARD_ID> or GUIXE_<TICKET_ID>
    memo_suffix = clean_card if clean_card else (clean_ticket[-8:] if clean_ticket else "UTH")
    memo = f"GUIXE {memo_suffix}".strip()

    qr_image_url = build_vietqr_url(
        amount=amount,
        add_info=memo,
        bank_id=target_bank,
        account_no=target_account,
        account_name=target_name,
    )

    return {
        "bank_id": target_bank,
        "account_no": target_account,
        "account_name": target_name,
        "amount": int(amount),
        "memo": memo,
        "card_id": clean_card,
        "ticket_id": clean_ticket,
        "qr_image_url": qr_image_url,
    }
