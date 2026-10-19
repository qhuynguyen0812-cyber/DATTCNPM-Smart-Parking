import api.main as api_main
from fastapi.testclient import TestClient


def test_jwt_login_and_me(monkeypatch):
    client = TestClient(api_main.app)
    monkeypatch.setattr(api_main, "authenticate_streamlit_user", lambda username, password: api_main.AuthUser(username="operator", role="operator"))

    login = client.post("/auth/login", data={"username": "operator", "password": "StrongPass123"})

    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"] == {"username": "operator", "role": "operator"}


def test_jwt_rejects_tampered_token(monkeypatch):
    client = TestClient(api_main.app)
    monkeypatch.setattr(api_main, "authenticate_streamlit_user", lambda username, password: api_main.AuthUser(username="viewer", role="viewer"))
    token = client.post("/auth/login", data={"username": "viewer", "password": "StrongPass123"}).json()["access_token"]
    bad = token + "x"

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {bad}"})

    assert response.status_code == 401


def test_viewer_jwt_rejected_for_write(monkeypatch):
    client = TestClient(api_main.app)
    monkeypatch.setattr(api_main, "authenticate_streamlit_user", lambda username, password: api_main.AuthUser(username="viewer", role="viewer"))
    token = client.post("/auth/login", data={"username": "viewer", "password": "StrongPass123"}).json()["access_token"]

    response = client.post("/devices/barrier/open", headers={"Authorization": f"Bearer {token}"}, data={"lane_id": "lane-1", "reason": "test"})

    assert response.status_code == 403
