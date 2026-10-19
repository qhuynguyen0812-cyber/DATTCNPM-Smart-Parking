from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.auth import register_streamlit_user
from backend.db import fetch_app_user, init_db

DEMO_USERS = [
    ("admin", "ItsDemo@2026A", "admin"),
    ("operator", "ItsDemo@2026O", "operator"),
    ("viewer", "ItsDemo@2026V", "viewer"),
]


def seed_demo_users() -> list[str]:
    init_db()
    messages: list[str] = []
    for username, password, role in DEMO_USERS:
        existing = fetch_app_user(username)
        if existing:
            messages.append(f"SKIP {username}: already exists as {existing.get('role')}")
            continue
        ok, message = register_streamlit_user(username, password, role=role)  # type: ignore[arg-type]
        status = "OK" if ok else "FAIL"
        messages.append(f"{status} {username}: {message}")
    return messages


def main() -> int:
    for line in seed_demo_users():
        print(line.encode("ascii", errors="replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
