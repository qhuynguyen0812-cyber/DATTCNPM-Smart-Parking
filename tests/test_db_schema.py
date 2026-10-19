from pathlib import Path
import sqlite3
import sys

import pytest

pytestmark = pytest.mark.integration


from backend.db import append_audit_log, apply_migrations, fetch_audit_logs


def test_apply_migrations_creates_schema_version(tmp_path):
    db_path = tmp_path / "schema.db"
    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 2


def test_apply_migrations_is_idempotent(tmp_path):
    db_path = tmp_path / "schema.db"
    apply_migrations(db_path)
    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    conn.close()

    assert rows == [(1,), (2,)]


def test_apply_migrations_migrates_legacy_schema(tmp_path):
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE parking_logs (
            ticket_id TEXT PRIMARY KEY,
            plate_entry TEXT,
            entry_time TEXT,
            status TEXT,
            ocr_confidence REAL
        )
        """
    )
    conn.execute(
        "INSERT INTO parking_logs(ticket_id, plate_entry, entry_time, status, ocr_confidence) VALUES (?, ?, ?, ?, ?)",
        ("T1", "66-B1 069.99", "2026-04-25T10:00:00", "IN_PARKING", 0.87),
    )
    conn.execute(
        """
        CREATE TABLE app_users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )
    conn.execute("INSERT INTO app_users(username, password_hash, role) VALUES (?, ?, ?)", ("operator", "hash", "operator"))
    conn.commit()
    conn.close()

    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    parking_columns = {row[1] for row in conn.execute("PRAGMA table_info('parking_logs')").fetchall()}
    user_columns = {row[1] for row in conn.execute("PRAGMA table_info('app_users')").fetchall()}
    migrated_confidence = conn.execute("SELECT entry_ocr_confidence FROM parking_logs WHERE ticket_id = 'T1'").fetchone()[0]
    is_active = conn.execute("SELECT is_active FROM app_users WHERE username = 'operator'").fetchone()[0]
    conn.close()

    assert {"entry_ocr_engine", "exit_ocr_engine", "entry_ocr_text", "exit_ocr_text"}.issubset(parking_columns)
    assert "is_active" in user_columns
    assert migrated_confidence == 0.87
    assert is_active == 1


def test_apply_migrations_creates_indexes(tmp_path):
    db_path = tmp_path / "schema.db"
    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("PRAGMA index_list('parking_logs')").fetchall()
    conn.close()

    index_names = {row[1] for row in rows}
    assert "idx_parking_logs_status_entry_time" in index_names
    assert "idx_parking_logs_entry_time" in index_names


def test_apply_migrations_adds_ocr_engine_columns(tmp_path):
    db_path = tmp_path / "schema.db"
    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("PRAGMA table_info('parking_logs')").fetchall()
    conn.close()

    column_names = {row[1] for row in rows}
    assert "entry_ocr_engine" in column_names
    assert "exit_ocr_engine" in column_names
    assert "entry_ocr_text" in column_names
    assert "exit_ocr_text" in column_names
    assert "entry_manual_override" in column_names
    assert "exit_manual_override" in column_names


def test_apply_migrations_creates_audit_logs_table(tmp_path):
    db_path = tmp_path / "schema.db"
    apply_migrations(db_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("PRAGMA table_info('audit_logs')").fetchall()
    conn.close()

    column_names = {row[1] for row in rows}
    assert {"actor_username", "actor_role", "action", "target_type", "target_id", "details_json", "created_at"}.issubset(column_names)


def test_append_and_fetch_audit_logs(tmp_path):
    db_path = tmp_path / "schema.db"
    apply_migrations(db_path)

    ok = append_audit_log("admin", "admin", "user_created", target_type="app_user", target_id="operator01", details_json='{"role":"operator"}', db_path=db_path)
    assert ok is True

    df = fetch_audit_logs(db_path)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["actor_username"] == "admin"
    assert row["action"] == "user_created"
    assert row["target_id"] == "operator01"
