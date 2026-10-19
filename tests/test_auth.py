import pytest

from backend import auth
from backend.auth import AuthUser, require_role

pytestmark = pytest.mark.unit


def test_parse_static_bearer_token_returns_matching_role(monkeypatch):
    monkeypatch.setattr(auth, "API_ALLOW_STATIC_TOKENS", True)
    monkeypatch.setattr(
        auth,
        "API_BEARER_TOKENS",
        {"admin": "admin-token", "operator": "operator-token", "viewer": "viewer-token"},
    )

    assert auth.parse_static_bearer_token("operator-token") == AuthUser(username="operator", role="operator")


@pytest.mark.parametrize("token", [None, "", "wrong-token"])
def test_parse_static_bearer_token_rejects_empty_or_unknown(monkeypatch, token):
    monkeypatch.setattr(auth, "API_ALLOW_STATIC_TOKENS", True)
    monkeypatch.setattr(auth, "API_BEARER_TOKENS", {"admin": "admin-token"})

    assert auth.parse_static_bearer_token(token) is None


def test_require_role_allows_matching_role():
    user = AuthUser(username="operator", role="operator")

    assert require_role(user, {"admin", "operator"}) is user


def test_require_role_rejects_viewer_for_write():
    user = AuthUser(username="viewer", role="viewer")

    with pytest.raises(PermissionError, match="Forbidden"):
        require_role(user, {"admin", "operator"})


def test_register_streamlit_user_rejects_invalid_username(monkeypatch):
    monkeypatch.setattr(auth, "get_streamlit_users", lambda: [])
    monkeypatch.setattr(auth, "fetch_app_user", lambda username: None)

    ok, message = auth.register_streamlit_user("bad user!", "abc12345")

    assert ok is False
    assert "Tên đăng nhập" in message


def test_register_streamlit_user_rejects_weak_password(monkeypatch):
    monkeypatch.setattr(auth, "get_streamlit_users", lambda: [])
    monkeypatch.setattr(auth, "fetch_app_user", lambda username: None)

    ok, message = auth.register_streamlit_user("operator01", "12345678")

    assert ok is False
    assert "10 ký tự" in message


def test_register_streamlit_user_rejects_duplicate_db_username(monkeypatch):
    monkeypatch.setattr(auth, "get_streamlit_users", lambda: [])
    monkeypatch.setattr(auth, "fetch_app_user", lambda username: {"username": username})

    ok, message = auth.register_streamlit_user("operator01", "StrongPass123")

    assert ok is False
    assert "đã tồn tại" in message


def test_register_streamlit_user_creates_db_user(monkeypatch):
    created = {}

    monkeypatch.setattr(auth, "get_streamlit_users", lambda: [])
    monkeypatch.setattr(auth, "fetch_app_user", lambda username: None)
    monkeypatch.setattr(auth, "create_app_user", lambda username, password_hash, role="viewer": created.setdefault("payload", (username, password_hash, role)) or True)

    ok, message = auth.register_streamlit_user("operator01", "StrongPass123", role="operator")

    assert ok is True
    assert message == "Đăng ký tài khoản thành công"
    assert created["payload"][0] == "operator01"
    assert created["payload"][1].startswith(auth.PASSWORD_SCHEME)
    assert created["payload"][2] == "operator"


def test_authenticate_streamlit_user_rejects_inactive_db_user(monkeypatch):
    monkeypatch.setattr(
        auth,
        "fetch_app_user",
        lambda username: {"username": username, "password_hash": "hash", "role": "viewer", "is_active": 0},
    )

    assert auth.authenticate_streamlit_user("viewer01", "StrongPass123") is None


def test_change_streamlit_password_rejects_wrong_current_password(monkeypatch):
    monkeypatch.setattr(auth, "authenticate_streamlit_user", lambda username, password: None)

    ok, message = auth.change_streamlit_password("viewer01", "wrong", "StrongPass123")

    assert ok is False
    assert "Mật khẩu hiện tại" in message


def test_change_streamlit_password_rejects_same_password(monkeypatch):
    monkeypatch.setattr(auth, "authenticate_streamlit_user", lambda username, password: AuthUser(username=username, role="viewer"))

    ok, message = auth.change_streamlit_password("viewer01", "StrongPass123", "StrongPass123")

    assert ok is False
    assert "khác mật khẩu hiện tại" in message
