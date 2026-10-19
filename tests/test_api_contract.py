import pytest

pytestmark = pytest.mark.api


from fastapi.testclient import TestClient
import pandas as pd

import api.main as api_main


def test_health_endpoint():
    client = TestClient(api_main.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_response_includes_request_context_headers():
    client = TestClient(api_main.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert float(response.headers["X-Process-Time-Ms"]) >= 0


def test_logs_requires_token_or_configuration():
    client = TestClient(api_main.app)
    response = client.get("/logs")

    assert response.status_code in {401, 503}


def test_logs_returns_records_with_token(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(
        api_main,
        "fetch_logs",
        lambda: pd.DataFrame([{"ticket_id": "T1", "plate_entry": "66-B1 069.99", "status": "IN_PARKING"}]),
    )
    monkeypatch.setattr(api_main, "API_TOKEN", "test-api-token")

    response = client.get("/logs", headers={"x-api-token": "test-api-token"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["count"] == 1
    assert payload["total"] == 1
    assert payload["items"][0]["ticket_id"] == "T1"


def test_logs_support_pagination(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(
        api_main,
        "fetch_logs",
        lambda: pd.DataFrame([
            {"ticket_id": "T1", "status": "IN_PARKING"},
            {"ticket_id": "T2", "status": "IN_PARKING"},
            {"ticket_id": "T3", "status": "COMPLETED"},
        ]),
    )
    monkeypatch.setattr(api_main, "API_TOKEN", "test-api-token")

    response = client.get("/logs?limit=1&offset=1", headers={"x-api-token": "test-api-token"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 1
    assert payload["offset"] == 1
    assert payload["total"] == 3
    assert payload["items"] == [{"ticket_id": "T2", "status": "IN_PARKING"}]


def test_logs_support_status_filter(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(
        api_main,
        "fetch_logs",
        lambda: pd.DataFrame([
            {"ticket_id": "T-IN", "status": "IN_PARKING"},
            {"ticket_id": "T-OUT", "status": "COMPLETED"},
        ]),
    )
    monkeypatch.setattr(api_main, "API_TOKEN", "test-api-token")

    response = client.get("/logs?status=IN_PARKING", headers={"x-api-token": "test-api-token"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"] == [{"ticket_id": "T-IN", "status": "IN_PARKING"}]


def test_logs_support_ticket_id_filter(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(
        api_main,
        "fetch_logs",
        lambda: pd.DataFrame([
            {"ticket_id": "T1", "status": "IN_PARKING"},
            {"ticket_id": "ABC-2", "status": "COMPLETED"},
        ]),
    )
    monkeypatch.setattr(api_main, "API_TOKEN", "test-api-token")

    response = client.get("/logs?ticket_id=abc", headers={"x-api-token": "test-api-token"})

    assert response.status_code == 200
    assert response.json()["items"] == [{"ticket_id": "ABC-2", "status": "COMPLETED"}]


def test_logs_accept_bearer_read_access(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "fetch_logs", lambda: pd.DataFrame([{"ticket_id": "T1"}]))
    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="viewer", role="viewer"))

    response = client.get("/logs", headers={"Authorization": "Bearer test-viewer"})
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_logs_prefer_x_api_token_when_present(monkeypatch):
    client = TestClient(api_main.app)
    called = {"token": 0, "bearer": 0}

    def fake_require_token(value=""):
        called["token"] += 1
        return None

    def fake_require_bearer_user(value=""):
        called["bearer"] += 1
        raise AssertionError("bearer auth should not be used when x-api-token is present")

    monkeypatch.setattr(api_main, "fetch_logs", lambda: pd.DataFrame(columns=["ticket_id"]))
    monkeypatch.setattr(api_main, "require_token", fake_require_token)
    monkeypatch.setattr(api_main, "require_bearer_user", fake_require_bearer_user)

    response = client.get("/logs", headers={"x-api-token": "token-present", "Authorization": "Bearer ignored"})
    assert response.status_code == 200
    assert called == {"token": 1, "bearer": 0}


def test_active_tickets_accepts_viewer_bearer(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(
        api_main,
        "get_active_tickets",
        lambda: pd.DataFrame([{"ticket_id": "T1", "plate_entry": "66-B1 069.99", "entry_time": "2026-04-25T10:00:00"}]),
    )
    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="viewer", role="viewer"))

    response = client.get("/tickets/active", headers={"Authorization": "Bearer viewer-token"})

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_active_tickets_accepts_x_api_token(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "get_active_tickets", lambda: pd.DataFrame([{"ticket_id": "T1"}]))
    monkeypatch.setattr(api_main, "API_TOKEN", "test-api-token")

    response = client.get("/tickets/active", headers={"x-api-token": "test-api-token"})

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_ocr_hides_internal_paths_by_default(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "save_uploaded_file", lambda file, prefix: "saved.jpg")
    monkeypatch.setattr(api_main, "process_plate_image", lambda path: type("P", (), {"ocr": {"annotated_path": "annotated.jpg", "confidence": 0.8, "text": "66-B1 069.99"}})())
    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="viewer", role="viewer"))
    monkeypatch.setattr(api_main, "API_EXPOSE_INTERNAL_PATHS", False)

    response = client.post(
        "/ocr",
        headers={"Authorization": "Bearer test-viewer"},
        files={"file": ("plate.jpg", b"fake-image", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "image_path" not in payload
    assert "annotated_path" not in payload["ocr"]


def test_ocr_can_expose_internal_paths_when_enabled(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "save_uploaded_file", lambda file, prefix: "saved.jpg")
    monkeypatch.setattr(api_main, "process_plate_image", lambda path: type("P", (), {"ocr": {"annotated_path": "annotated.jpg", "confidence": 0.8, "text": "66-B1 069.99"}})())
    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="viewer", role="viewer"))
    monkeypatch.setattr(api_main, "API_EXPOSE_INTERNAL_PATHS", True)

    response = client.post(
        "/ocr",
        headers={"Authorization": "Bearer test-viewer"},
        files={"file": ("plate.jpg", b"fake-image", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["image_path"] == "saved.jpg"
    assert payload["ocr"]["annotated_path"] == "annotated.jpg"


def test_write_endpoint_rejects_viewer(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="viewer", role="viewer"))

    response = client.post(
        "/vehicle/entry",
        headers={"Authorization": "Bearer test-viewer"},
        files={"file": ("plate.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 403


def test_write_endpoint_accepts_operator(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "process_plate_image", lambda path: type("P", (), {"ocr": {"annotated_path": "annotated.jpg", "confidence": 0.8}, "plate_text": "66-B1 069.99"})())
    monkeypatch.setattr(api_main, "save_uploaded_file", lambda file, prefix: "saved.jpg")
    monkeypatch.setattr(api_main, "confirm_vehicle_entry", lambda *args, **kwargs: {"success": True, "ticket_id": "T1"})
    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="operator", role="operator"))

    response = client.post(
        "/vehicle/entry",
        headers={"Authorization": "Bearer test-operator"},
        files={"file": ("plate.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 201
    assert response.json()["result"]["ticket_id"] == "T1"


def test_write_endpoint_rejects_invalid_bearer(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: None)

    response = client.post(
        "/vehicle/entry",
        headers={"Authorization": "Bearer bad-token"},
        files={"file": ("plate.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 401


def test_map_business_failure_validation_error():
    response = api_main.map_business_failure({"success": False, "message": "Invalid plate text: partial plate"}, resource="ticket")

    assert response.status_code == 400
    assert b"VALIDATION_ERROR" in response.body


def test_vehicle_entry_returns_business_conflict(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "process_plate_image", lambda path: type("P", (), {"ocr": {"annotated_path": "annotated.jpg", "confidence": 0.8}, "plate_text": "66-B1 069.99"})())
    monkeypatch.setattr(api_main, "save_uploaded_file", lambda file, prefix: "saved.jpg")
    monkeypatch.setattr(api_main, "confirm_vehicle_entry", lambda *args, **kwargs: {"success": False, "message": "Vehicle already has an active ticket", "ticket_id": "T1"})
    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="admin", role="admin"))

    response = client.post(
        "/vehicle/entry",
        headers={"Authorization": "Bearer test-admin"},
        files={"file": ("plate.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "TICKET_CONFLICT"


def test_vehicle_exit_returns_not_found(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(api_main, "process_plate_image", lambda path: type("P", (), {"ocr": {"annotated_path": "annotated.jpg", "confidence": 0.8}, "plate_text": "66-B1 069.99"})())
    monkeypatch.setattr(api_main, "save_uploaded_file", lambda file, prefix: "saved.jpg")
    monkeypatch.setattr(api_main, "confirm_vehicle_exit", lambda *args, **kwargs: {"success": False, "message": "Ticket ID not found"})
    monkeypatch.setattr(api_main, "parse_static_bearer_token", lambda token: api_main.AuthUser(username="admin", role="admin"))

    response = client.post(
        "/vehicle/exit",
        headers={"Authorization": "Bearer test-admin"},
        data={"ticket_id": "T404"},
        files={"file": ("plate.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "TICKET_NOT_FOUND"


def test_logs_support_time_range_filter(monkeypatch):
    client = TestClient(api_main.app)

    monkeypatch.setattr(
        api_main,
        "fetch_logs",
        lambda: pd.DataFrame([
            {"ticket_id": "T1", "entry_time": "2026-04-25 08:00:00"},
            {"ticket_id": "T2", "entry_time": "2026-04-26 12:00:00"},
            {"ticket_id": "T3", "entry_time": "2026-04-27 18:00:00"},
        ]),
    )
    monkeypatch.setattr(api_main, "API_TOKEN", "test-api-token")

    response = client.get("/logs?from_time=2026-04-26&to_time=2026-04-26", headers={"x-api-token": "test-api-token"})

    assert response.status_code == 200
    assert response.json()["items"] == [{"ticket_id": "T2", "entry_time": "2026-04-26 12:00:00"}]
