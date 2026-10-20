"""
MBBank Automated Bridge & Webhook Dispatcher.
Connects MBBank balance change notifications / API-MBBANK-PYTHON to the Smart Parking Backend.
Supports live polling, file watcher on bill.json, and manual simulation for demonstrations.
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None

from backend.payment_reconciliation import reconcile_bank_transaction

logger = logging.getLogger(__name__)


def simulate_bank_credit(
    card_id: str,
    amount: int = 5000,
    transaction_id: str | None = None,
    account_no: str = "0325617476",
    backend_url: str | None = None,
) -> dict[str, Any]:
    """Simulate an incoming MBBank transfer from a student scanning VietQR."""
    trans_id = transaction_id or f"MB_SIM_{int(time.time() * 1000)}"
    memo = f"GUIXE {card_id}".strip()

    payload = {
        "transaction_id": trans_id,
        "amount": int(amount),
        "description": memo,
        "account_no": account_no,
        "transactionDate": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    if backend_url and requests is not None:
        try:
            resp = requests.post(f"{backend_url.rstrip('/')}/payment/webhook", json=payload, timeout=5)
            return resp.json()
        except Exception as exc:
            logger.warning("HTTP post to %s failed: %s, falling back to direct reconcile", backend_url, exc)

    # Direct in-process reconcile fallback
    return reconcile_bank_transaction(payload)


def watch_bill_json(
    bill_path: str = "bill.json",
    backend_url: str = "http://localhost:8000",
    poll_interval: float = 2.0,
):
    """Watch bill.json output from API-MBBANK-PYTHON-main and automatically forward new transactions."""
    path = Path(bill_path)
    processed_indices = set()
    logger.info("Watching %s for incoming MBBank transactions...", path)

    while True:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    bills = json.load(f)

                for idx, bill in enumerate(bills):
                    if idx in processed_indices:
                        continue
                    if bill.get("type") == "credit" or bill.get("amount", 0) > 0:
                        payload = {
                            "transaction_id": bill.get("transactionId") or f"BILL_{idx}_{int(time.time())}",
                            "amount": bill.get("amount"),
                            "description": bill.get("description", ""),
                            "account_no": bill.get("account", "0325617476"),
                            "transactionDate": bill.get("time"),
                        }
                        res = reconcile_bank_transaction(payload)
                        logger.info("Reconciled transaction [%d]: %s", idx, res.get("message"))
                    processed_indices.add(idx)
        except Exception as exc:
            logger.debug("Polling error: %s", exc)

        time.sleep(poll_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MBBank Bridge for UTH Smart Parking")
    parser.add_argument("--simulate", action="store_true", help="Simulate a bank transfer")
    parser.add_argument("--card-id", type=str, default="CARD_UTH_001", help="RFID Card ID")
    parser.add_argument("--amount", type=int, default=5000, help="Payment amount in VND")
    parser.add_argument("--watch-file", type=str, help="Watch bill.json from API-MBBANK-PYTHON")
    args = parser.parse_args()

    if args.simulate:
        result = simulate_bank_credit(card_id=args.card_id, amount=args.amount)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.watch_file:
        watch_bill_json(bill_path=args.watch_file)
    else:
        parser.print_help()
