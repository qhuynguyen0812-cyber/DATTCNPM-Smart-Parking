from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db import apply_migrations


def test_apply_migrations_creates_schema_version(tmp_path):
    db_path = tmp_path / "schema.db"
    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 1
