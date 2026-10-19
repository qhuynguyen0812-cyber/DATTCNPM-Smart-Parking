import sqlite3

from scripts.validate_runtime_db import validate_runtime_db


def test_runtime_validator_flags_invalid_completed_ticket(tmp_path):
    db_path = tmp_path / "bad.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE parking_logs (ticket_id TEXT PRIMARY KEY, status TEXT, exit_time TEXT, entry_time TEXT)")
        conn.execute("INSERT INTO parking_logs(ticket_id, status, entry_time, exit_time) VALUES ('T1', 'COMPLETED', '2026-01-01', NULL)")

    issues = validate_runtime_db(db_path)

    assert any(issue.code == "COMPLETED_WITHOUT_EXIT_TIME" for issue in issues)
