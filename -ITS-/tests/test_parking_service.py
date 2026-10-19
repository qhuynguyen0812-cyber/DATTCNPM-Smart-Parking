from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import db as db_module
from backend import parking_service as parking_module


def test_vehicle_entry_rejects_invalid_plate(tmp_path):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    parking_module.DB_PATH = db_path

    result = parking_module.vehicle_entry("???")

    assert result["success"] is False
    assert result["message"] == "Invalid plate text"


def test_vehicle_entry_normalizes_and_persists_plate(tmp_path):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    parking_module.DB_PATH = db_path

    result = parking_module.vehicle_entry("66b1\n069.99", ocr_confidence=1.7)

    assert result["success"] is True
    assert result["plate_entry"] == "66-B1 069.99"

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT plate_entry, status, match_result, ocr_confidence FROM parking_logs WHERE ticket_id = ?", (result["ticket_id"],)).fetchone()
    conn.close()

    assert row == ("66-B1 069.99", "IN_PARKING", "PENDING", 1.0)


def test_vehicle_exit_returns_mismatch_for_different_plate(tmp_path):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    parking_module.DB_PATH = db_path

    entry = parking_module.vehicle_entry("66B106999")
    result = parking_module.vehicle_exit(entry["ticket_id"], "67B106999")

    assert result["success"] is True
    assert result["match_result"] == "MISMATCH"


def test_vehicle_exit_rejects_completed_ticket(tmp_path):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    parking_module.DB_PATH = db_path

    entry = parking_module.vehicle_entry("66B106999")
    first_exit = parking_module.vehicle_exit(entry["ticket_id"], "66B106999")
    second_exit = parking_module.vehicle_exit(entry["ticket_id"], "66B106999")

    assert first_exit["success"] is True
    assert second_exit["success"] is False
    assert second_exit["message"] == "Vehicle already checked out"
