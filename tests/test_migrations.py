import sqlite3

from backend.migrations import run_migrations


def test_migrations_are_idempotent(tmp_path):
    db_path = tmp_path / "runtime.db"

    run_migrations(db_path)
    run_migrations(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert {"parking_logs", "parking_events", "audit_logs", "app_users", "schema_migrations"}.issubset(tables)
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()]
        assert versions


def test_migration_preserves_legacy_parking_rows(tmp_path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE parking_logs (ticket_id TEXT PRIMARY KEY, plate_entry TEXT, entry_time TEXT, status TEXT)")
        conn.execute("INSERT INTO parking_logs(ticket_id, plate_entry, entry_time, status) VALUES ('T1', '66-B1 123.45', '2026-01-01T00:00:00', 'IN_PARKING')")

    run_migrations(db_path)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT plate_entry, status FROM parking_logs WHERE ticket_id='T1'").fetchone()
        columns = {row[1] for row in conn.execute("PRAGMA table_info(parking_logs)").fetchall()}
        assert row == ("66-B1 123.45", "IN_PARKING")
        assert "review_reason" in columns
