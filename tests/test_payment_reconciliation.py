import pytest
from fastapi.testclient import TestClient

from api.main import app
from backend.auth import AuthUser, create_session_token
from backend.db import apply_migrations, fetch_ticket_detail, get_zone_status
from backend.parking_service import vehicle_entry
from backend.payment_reconciliation import (
    extract_parking_reference,
    is_bank_transaction_processed,
    reconcile_bank_transaction,
)
from integrations.barrier_service import barrier_simulator


def test_extract_parking_reference():
    res1 = extract_parking_reference("GUIXE CARD_001")
    assert res1["card_id"] == "CARD_001"

    res2 = extract_parking_reference("CHUYEN TIEN GUIXE CARD_UTH_888 XIN CAM ON")
    assert res2["card_id"] == "CARD_UTH_888"

    res3 = extract_parking_reference("GUIXE T20261020150000ABCD")
    assert res3["ticket_id"] == "T20261020150000ABCD"

    res4 = extract_parking_reference("NOI DUNG KHONG LIEN QUAN")
    assert res4["card_id"] is None
    assert res4["ticket_id"] is None


def test_auto_reconciliation_and_barrier_open(tmp_path, monkeypatch):
    test_db = tmp_path / "test_reconcile.db"
    apply_migrations(test_db)
    monkeypatch.setattr("backend.db.DB_PATH", test_db)
    monkeypatch.setattr("backend.parking_service.DB_PATH", test_db)
    monkeypatch.setattr("backend.payment_reconciliation.DB_PATH", test_db)

    # 1. Xe vào bãi, quẹt thẻ CARD_AUTO_1, vào Khu B (Zone B)
    entry_res = vehicle_entry(
        plate_text="59T1-88888",
        card_id="CARD_AUTO_1",
        zone_assigned="ZONE_B",
    )
    assert entry_res["success"] is True
    ticket_id = entry_res["ticket_id"]

    # Zone B occupancy tăng 1
    zone_b = get_zone_status("ZONE_B", test_db)
    assert zone_b["current_occupied"] == 1

    # 2. Sinh viên quét mã QR chuyển khoản 5.000đ từ MBBank
    payload = {
        "transaction_id": "MB_TRANS_9999",
        "amount": 5000,
        "description": "GUIXE CARD_AUTO_1",
        "account_no": "0325617476",
        "transactionDate": "2026-10-20 16:25:00",
    }

    initial_barrier_commands = len(barrier_simulator.commands)

    # 3. Webhook / Polling xử lý giao dịch
    reconcile_res = reconcile_bank_transaction(payload, db_path=test_db)
    assert reconcile_res["success"] is True
    assert reconcile_res["reconciled"] is True
    assert reconcile_res["ticket_id"] == ticket_id
    assert reconcile_res["card_id"] == "CARD_AUTO_1"
    assert reconcile_res["payment_status"] == "PAID"
    assert reconcile_res["ticket_status"] == "COMPLETED"

    # Kiểm tra Barrier đã được mở tự động
    assert len(barrier_simulator.commands) == initial_barrier_commands + 1
    last_cmd = barrier_simulator.commands[-1]
    assert last_cmd.action == "OPEN"
    assert "paid-5000" in last_cmd.reason

    # Kiểm tra vé trong CSDL đã chuyển trạng thái PAID và COMPLETED
    ticket = fetch_ticket_detail(ticket_id, test_db)
    assert ticket["payment_status"] == "PAID"
    assert ticket["status"] == "COMPLETED"
    assert ticket["payment_method"] == "VIETQR"

    # Zone B occupancy giảm lại về 0
    zone_b_after = get_zone_status("ZONE_B", test_db)
    assert zone_b_after["current_occupied"] == 0

    # 4. Kiểm tra Idempotency (gửi lại giao dịch cũ không bị xử lý lặp)
    dup_res = reconcile_bank_transaction(payload, db_path=test_db)
    assert dup_res["success"] is True
    assert dup_res.get("already_processed") is True
    assert len(barrier_simulator.commands) == initial_barrier_commands + 1


def test_reconciliation_underpaid_rejection(tmp_path, monkeypatch):
    test_db = tmp_path / "test_underpaid.db"
    apply_migrations(test_db)
    monkeypatch.setattr("backend.db.DB_PATH", test_db)
    monkeypatch.setattr("backend.parking_service.DB_PATH", test_db)
    monkeypatch.setattr("backend.payment_reconciliation.DB_PATH", test_db)

    # Xe vào
    entry = vehicle_entry("59T2-11111", card_id="CARD_UNDERPAID", zone_assigned="ZONE_A")
    ticket_id = entry["ticket_id"]

    # Chuyển thiếu tiền (chỉ chuyển 2.000đ trong khi vé là 5.000đ)
    payload = {
        "transaction_id": "MB_TRANS_LOW",
        "amount": 2000,
        "description": "GUIXE CARD_UNDERPAID",
    }
    res = reconcile_bank_transaction(payload, db_path=test_db)
    assert res["success"] is False
    assert res["reconciled"] is False
    assert "Underpaid" in res["message"]

    # Vé vẫn chưa được thanh toán
    ticket = fetch_ticket_detail(ticket_id, test_db)
    assert ticket["payment_status"] != "PAID"


def test_api_payment_webhook_endpoint(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api_webhook.db"
    apply_migrations(test_db)
    monkeypatch.setattr("backend.db.DB_PATH", test_db)
    monkeypatch.setattr("backend.parking_service.DB_PATH", test_db)
    monkeypatch.setattr("backend.payment_reconciliation.DB_PATH", test_db)

    vehicle_entry("59T3-22222", card_id="CARD_WEBHOOK_01", zone_assigned="ZONE_C")

    client = TestClient(app)
    res = client.post(
        "/payment/webhook",
        json={
            "transaction_id": "TRANS_API_001",
            "amount": 5000,
            "description": "GUIXE CARD_WEBHOOK_01",
            "accountNo": "0325617476",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["result"]["reconciled"] is True
    assert data["result"]["card_id"] == "CARD_WEBHOOK_01"

    # Lấy danh sách giao dịch ngân hàng
    admin_user = AuthUser(username="admin", role="admin")
    token = create_session_token(admin_user)
    tx_res = client.get("/payment/transactions", headers={"Authorization": f"Bearer {token}"})
    assert tx_res.status_code == 200
    tx_data = tx_res.json()
    assert tx_data["count"] >= 1
    assert any(tx["transaction_id"] == "TRANS_API_001" for tx in tx_data["items"])
