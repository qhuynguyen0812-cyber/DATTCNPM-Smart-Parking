from fastapi.testclient import TestClient

from api.main import app
from backend.auth import AuthUser, create_session_token
from backend.config import DEFAULT_PARKING_FEE, SCHEMA_VERSION
from backend.db import apply_migrations, get_zone_status


def test_api_health_schema_version():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["schema_version"] == SCHEMA_VERSION


def test_api_zones_status_endpoint(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api_zones.db"
    apply_migrations(test_db)
    monkeypatch.setattr("backend.db.DB_PATH", test_db)
    monkeypatch.setattr("backend.parking_service.DB_PATH", test_db)

    client = TestClient(app)
    operator_user = AuthUser(username="operator", role="operator")
    token = create_session_token(operator_user)

    res = client.get("/zones/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "zones" in data
    assert len(data["zones"]) == 4
    assert data["total_capacity"] == 250 + 450 + 450 + 600
    assert data["total_available"] == data["total_capacity"]


def test_api_payment_vietqr_endpoint():
    client = TestClient(app)
    operator_user = AuthUser(username="operator", role="operator")
    token = create_session_token(operator_user)

    res = client.get("/payment/vietqr?card_id=UTH_CARD_123&amount=5000", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["card_id"] == "UTH_CARD_123"
    assert data["amount"] == 5000
    assert "qr_image_url" in data
    assert "GUIXE" in data["memo"]


def test_api_zones_recalculate_endpoint(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api_recalc.db"
    apply_migrations(test_db)
    monkeypatch.setattr("backend.db.DB_PATH", test_db)
    monkeypatch.setattr("backend.parking_service.DB_PATH", test_db)

    client = TestClient(app)
    admin_user = AuthUser(username="admin", role="admin")
    token = create_session_token(admin_user)

    res = client.post("/zones/recalculate", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "recalculated_occupancies" in data
