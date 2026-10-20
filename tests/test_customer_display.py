from fastapi.testclient import TestClient

from api.main import app
from backend.customer_display_state import (
    get_customer_display_state,
    trigger_checkout_display,
    trigger_idle_display,
    trigger_success_display,
)


def test_customer_display_state_transitions():
    trigger_idle_display(lane_name="CỔNG 2 — LÀN XẢ B")
    s1 = get_customer_display_state()
    assert s1["state"] == "IDLE"
    assert s1["lane_name"] == "CỔNG 2 — LÀN XẢ B"

    # Xe ra bãi
    trigger_checkout_display(
        plate_number="59X1-99999",
        fee=10000,
        overnight_surcharge=5000,
        card_id="CARD_TEST_01",
    )
    s2 = get_customer_display_state()
    assert s2["state"] == "CHECKOUT"
    assert s2["plate_number"] == "59X1-99999"
    assert s2["fee"] == 10000
    assert s2["overnight_surcharge"] == 5000
    assert s2["qr_url"] is not None
    assert "0325617476" in s2["qr_url"]

    # Thanh toán thành công
    trigger_success_display(plate_number="59X1-99999", amount=10000)
    s3 = get_customer_display_state()
    assert s3["state"] == "SUCCESS"
    assert s3["fee"] == 10000


def test_api_customer_display_endpoints():
    client = TestClient(app)

    # 1. Tải trang HTML màn hình phụ
    res_html = client.get("/customer-display")
    assert res_html.status_code == 200
    assert "UTH Smart Parking" in res_html.text
    assert "checkout-qr-img" in res_html.text

    # 2. Truy vấn state qua API
    res_state = client.get("/display/state")
    assert res_state.status_code == 200
    assert res_state.json()["ok"] is True
    assert "state" in res_state.json()

    # 3. Cập nhật state qua API
    res_update = client.post(
        "/display/state",
        json={"state": "CHECKOUT", "plate_number": "66B1-12345", "fee": 5000},
    )
    assert res_update.status_code == 200
    assert res_update.json()["state"]["state"] == "CHECKOUT"
    assert res_update.json()["state"]["plate_number"] == "66B1-12345"

    # 4. Reset display
    res_reset = client.post("/display/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["state"]["state"] == "IDLE"
