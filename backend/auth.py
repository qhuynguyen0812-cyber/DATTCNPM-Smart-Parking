import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Literal

from backend.config import (
    API_ALLOW_STATIC_TOKENS,
    API_BEARER_TOKENS,
    API_JWT_EXPIRE_MINUTES,
    API_JWT_SECRET,
    STREAMLIT_ADMIN_PASSWORD,
    STREAMLIT_ADMIN_USERNAME,
    STREAMLIT_OPERATOR_PASSWORD,
    STREAMLIT_OPERATOR_USERNAME,
    STREAMLIT_VIEWER_PASSWORD,
    STREAMLIT_VIEWER_USERNAME,
)
from backend.db import append_audit_log, create_app_user, fetch_app_user, update_app_user_password_hash, update_login_failure, update_login_success

Role = Literal["admin", "operator", "viewer"]
ALL_ROLES: set[Role] = {"admin", "operator", "viewer"}
READ_ROLES: set[Role] = ALL_ROLES.copy()
WRITE_ROLES: set[Role] = {"admin", "operator"}


@dataclass(frozen=True)
class AuthUser:
    username: str
    role: Role


@dataclass(frozen=True)
class LoginUser:
    username: str
    password: str
    role: Role


def get_streamlit_users() -> list[LoginUser]:
    users: list[LoginUser] = []
    for username, password, role in [
        (STREAMLIT_ADMIN_USERNAME, STREAMLIT_ADMIN_PASSWORD, "admin"),
        (STREAMLIT_OPERATOR_USERNAME, STREAMLIT_OPERATOR_PASSWORD, "operator"),
        (STREAMLIT_VIEWER_USERNAME, STREAMLIT_VIEWER_PASSWORD, "viewer"),
    ]:
        if password:
            users.append(LoginUser(username=username, password=password, role=role))
    return users


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 120000
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


def _hash_password_legacy(password: str, username: str) -> str:
    seed = f"its::{(username or '').strip().lower()}::{password or ''}"
    return hashlib.sha256(seed.encode('utf-8')).hexdigest()


def _hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${derived}"


def _verify_password(password: str, stored_hash: str, username: str) -> tuple[bool, bool]:
    if not stored_hash:
        return False, False

    if "$" not in stored_hash:
        legacy_ok = hmac.compare_digest(stored_hash, _hash_password_legacy(password, username))
        return legacy_ok, legacy_ok

    try:
        scheme, iterations_text, salt, expected = stored_hash.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False, False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            (password or "").encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations_text),
        ).hex()
        return hmac.compare_digest(derived, expected), False
    except Exception:
        return False, False


def _safe_audit(actor_username: str | None, actor_role: str | None, action: str, **kwargs):
    try:
        append_audit_log(actor_username, actor_role, action, **kwargs)
    except Exception as exc:
        # Authentication must not fail just because the audit table is unavailable
        # in a test or partially initialized local database.
        logging.getLogger(__name__).warning("append_audit_log failed for %s: %s", action, exc)


def _is_locked(db_user: dict) -> bool:
    locked_until = db_user.get("locked_until")
    if not locked_until:
        return False
    try:
        return datetime.fromisoformat(str(locked_until)) > datetime.now()
    except ValueError:
        return False


def authenticate_streamlit_user(username: str, password: str) -> AuthUser | None:
    clean_username = (username or "").strip()
    clean_password = password or ""

    db_user = fetch_app_user(clean_username)
    if db_user:
        if not bool(db_user.get("is_active", 1)) or _is_locked(db_user):
            _safe_audit(clean_username, db_user.get("role"), "auth.login_blocked", target_type="user", target_id=clean_username)
            return None
        verified, needs_upgrade = _verify_password(clean_password, db_user.get("password_hash", ""), clean_username)
        if verified:
            if needs_upgrade:
                update_app_user_password_hash(clean_username, _hash_password(clean_password))
            update_login_success(clean_username)
            _safe_audit(clean_username, db_user.get("role"), "auth.login_success", target_type="user", target_id=clean_username)
            return AuthUser(username=db_user["username"], role=db_user["role"])
        failed_count = int(db_user.get("failed_login_count") or 0) + 1
        locked_until = None
        if failed_count >= MAX_FAILED_LOGINS:
            locked_until = (datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat(timespec="seconds")
        update_login_failure(clean_username, locked_until)
        _safe_audit(clean_username, db_user.get("role"), "auth.login_failure", target_type="user", target_id=clean_username)

    for user in get_streamlit_users():
        if clean_username == user.username and clean_password == user.password:
            return AuthUser(username=user.username, role=user.role)
    return None


def _validate_new_password(password: str, username: str = "") -> tuple[bool, str]:
    clean_password = password or ""
    if len(clean_password) < 10:
        return False, "Mật khẩu phải có ít nhất 10 ký tự"
    if username and username.lower() in clean_password.lower():
        return False, "Mật khẩu không được chứa tên đăng nhập"
    if not re.search(r"[a-z]", clean_password):
        return False, "Mật khẩu phải có chữ thường"
    if not re.search(r"[A-Z]", clean_password):
        return False, "Mật khẩu phải có chữ hoa"
    if not re.search(r"\d", clean_password):
        return False, "Mật khẩu phải có số"
    return True, ""


def register_streamlit_user(username: str, password: str, role: Role = "viewer") -> tuple[bool, str]:
    clean_username = (username or "").strip()
    clean_password = password or ""

    if not USERNAME_PATTERN.match(clean_username):
        return False, "Tên đăng nhập chỉ được chứa chữ, số, dấu chấm, gạch dưới hoặc gạch ngang, dài 3-32 ký tự"

    is_valid_password, password_message = _validate_new_password(clean_password, clean_username)
    if not is_valid_password:
        return False, password_message

    for user in get_streamlit_users():
        if clean_username == user.username:
            return False, "Tên đăng nhập đã tồn tại"

    existing = fetch_app_user(clean_username)
    if existing:
        return False, "Tên đăng nhập đã tồn tại"

    created = create_app_user(clean_username, _hash_password(clean_password), role=role)
    if not created:
        return False, "Không thể tạo tài khoản"
    return True, "Đăng ký tài khoản thành công"


def change_streamlit_password(username: str, current_password: str, new_password: str) -> tuple[bool, str]:
    clean_username = (username or "").strip()
    user = authenticate_streamlit_user(clean_username, current_password)
    if user is None:
        return False, "Mật khẩu hiện tại không đúng"

    is_valid_password, password_message = _validate_new_password(new_password, clean_username)
    if not is_valid_password:
        return False, password_message
    if current_password == new_password:
        return False, "Mật khẩu mới phải khác mật khẩu hiện tại"

    db_user = fetch_app_user(clean_username)
    if not db_user:
        return False, "Chỉ tài khoản đăng ký trong hệ thống mới có thể đổi mật khẩu tại đây"

    updated = update_app_user_password_hash(clean_username, _hash_password(new_password))
    if not updated:
        return False, "Không thể cập nhật mật khẩu"
    return True, "Đổi mật khẩu thành công"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign_token(header_b64: str, payload_b64: str) -> str:
    body = f"{header_b64}.{payload_b64}".encode("utf-8")
    return _b64url_encode(hmac.new(API_JWT_SECRET.encode("utf-8"), body, hashlib.sha256).digest())


def create_session_token(user: AuthUser, expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = now + timedelta(minutes=expires_minutes or API_JWT_EXPIRE_MINUTES)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.username,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": secrets.token_hex(12),
    }
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature_b64 = _sign_token(header_b64, payload_b64)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_session_token(token: str | None) -> AuthUser | None:
    clean = (token or "").strip()
    if not clean or clean.count(".") != 2:
        return None
    try:
        header_b64, payload_b64, signature_b64 = clean.split(".", 2)
        expected = _sign_token(header_b64, payload_b64)
        if not hmac.compare_digest(signature_b64, expected):
            return None
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if int(payload.get("exp") or 0) < int(datetime.now(timezone.utc).replace(tzinfo=None).timestamp()):
            return None
        username = str(payload.get("sub") or "").strip()
        role = str(payload.get("role") or "").strip()
        if role not in ALL_ROLES or not username:
            return None
        return AuthUser(username=username, role=role)  # type: ignore[arg-type]
    except Exception:
        return None


def parse_static_bearer_token(token: str | None) -> AuthUser | None:
    clean = (token or "").strip()
    if not clean:
        return None

    if not API_ALLOW_STATIC_TOKENS:
        return None
    for role, configured_token in API_BEARER_TOKENS.items():
        if configured_token and hmac.compare_digest(clean, configured_token):
            return AuthUser(username=role, role=role)
    return None


def require_role(user: AuthUser, allowed_roles: set[Role]) -> AuthUser:
    """Enforce role membership for already-authenticated API/UI identities."""
    if user.role not in allowed_roles:
        raise PermissionError("Forbidden")
    return user
