import sqlite3

import pandas as pd

from backend.config import DB_PATH, SCHEMA_VERSION


PARKING_LOGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS parking_logs (
    ticket_id TEXT PRIMARY KEY,
    plate_entry TEXT,
    plate_exit TEXT,
    entry_time TEXT,
    exit_time TEXT,
    status TEXT,
    match_result TEXT,
    entry_image_path TEXT,
    entry_detected_path TEXT,
    entry_plate_path TEXT,
    exit_image_path TEXT,
    exit_detected_path TEXT,
    exit_plate_path TEXT,
    ocr_confidence REAL
)
"""

SCHEMA_MIGRATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


def _connect(db_path=DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def apply_migrations(db_path=DB_PATH):
    with _connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(SCHEMA_MIGRATIONS_SCHEMA)
        cursor.execute(PARKING_LOGS_SCHEMA)
        cursor.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)", (SCHEMA_VERSION,))


def init_db(db_path=DB_PATH):
    apply_migrations(db_path)


def fetch_logs() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM parking_logs ORDER BY entry_time DESC", conn)


def get_active_tickets() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query("SELECT ticket_id, plate_entry, entry_time FROM parking_logs WHERE status = 'IN_PARKING' ORDER BY entry_time DESC", conn)

