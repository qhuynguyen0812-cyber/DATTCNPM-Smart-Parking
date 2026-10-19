from fastapi.testclient import TestClient

import api.main as api_main


def test_fe_business_screens_have_api_parity(monkeypatch):
    client = TestClient(api_main.app)
    admin = api_main.AuthUser(username="admin", role="admin")
    operator = api_main.AuthUser(username="operator", role="operator")
    viewer = api_main.AuthUser(username="viewer", role="viewer")

    admin_token = api_main.create_session_token(admin)
    operator_token = api_main.create_session_token(operator)
    viewer_token = api_main.create_session_token(viewer)

    read_endpoints = [
        "/logs",
        "/tickets/active",
        "/events",
        "/operations/summary",
        "/devices/status",
    ]
    for endpoint in read_endpoints:
        response = client.get(endpoint, headers={"Authorization": f"Bearer {viewer_token}"})
        assert response.status_code == 200, endpoint

    admin_endpoints = [
        "/audit-logs",
        "/admin/users",
    ]
    for endpoint in admin_endpoints:
        response = client.get(endpoint, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200, endpoint
        forbidden = client.get(endpoint, headers={"Authorization": f"Bearer {operator_token}"})
        assert forbidden.status_code == 403, endpoint

    barrier_ok = client.post("/devices/barrier/open", headers={"Authorization": f"Bearer {operator_token}"}, data={"lane_id": "lane-1", "reason": "contract-test"})
    assert barrier_ok.status_code == 200

    barrier_forbidden = client.post("/devices/barrier/open", headers={"Authorization": f"Bearer {viewer_token}"}, data={"lane_id": "lane-1", "reason": "contract-test"})
    assert barrier_forbidden.status_code == 403


def test_admin_user_api_parity(monkeypatch):
    client = TestClient(api_main.app)
    admin_token = api_main.create_session_token(api_main.AuthUser(username="admin", role="admin"))
    monkeypatch.setattr(api_main, "register_streamlit_user", lambda username, password, role="viewer": (True, "created"))
    monkeypatch.setattr(api_main, "update_app_user_role", lambda username, role: True)
    monkeypatch.setattr(api_main, "update_app_user_active", lambda username, is_active: True)
    monkeypatch.setattr(api_main, "delete_app_user", lambda username: True)

    headers = {"Authorization": f"Bearer {admin_token}"}
    assert client.post("/admin/users", headers=headers, data={"username": "newop", "password": "StrongPass123", "role": "operator"}).status_code == 201
    assert client.patch("/admin/users/newop/role", headers=headers, data={"role": "viewer"}).status_code == 200
    assert client.patch("/admin/users/newop/active", headers=headers, data={"is_active": "false"}).status_code == 200
    assert client.delete("/admin/users/newop", headers=headers).status_code == 200


def test_admin_user_actions_write_audit_log(monkeypatch):
    client = TestClient(api_main.app)
    admin_token = api_main.create_session_token(api_main.AuthUser(username="admin", role="admin"))
    monkeypatch.setattr(api_main, "register_streamlit_user", lambda username, password, role="viewer": (True, "created"))
    monkeypatch.setattr(api_main, "update_app_user_role", lambda username, role: True)
    monkeypatch.setattr(api_main, "update_app_user_active", lambda username, is_active: True)
    monkeypatch.setattr(api_main, "delete_app_user", lambda username: True)

    audit_calls = []
    monkeypatch.setattr(api_main, "append_audit_log", lambda *args, **kwargs: audit_calls.append((args, kwargs)) or True)

    headers = {"Authorization": f"Bearer {admin_token}"}
    client.post("/admin/users", headers=headers, data={"username": "newop", "password": "StrongPass123", "role": "operator"})
    client.patch("/admin/users/newop/role", headers=headers, data={"role": "viewer"})
    client.patch("/admin/users/newop/active", headers=headers, data={"is_active": "false"})
    client.delete("/admin/users/newop", headers=headers)

    actions = [args[2] for args, _ in audit_calls]
    assert "admin.user.create" in actions
    assert "admin.user.role" in actions
    assert "admin.user.active" in actions
    assert "admin.user.delete" in actions
