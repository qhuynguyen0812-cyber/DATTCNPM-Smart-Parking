from pathlib import Path
import sqlite3
import sys

import pytest

pytestmark = pytest.mark.integration


from backend import db as db_module
from backend import parking_service as parking_module


def test_vehicle_entry_rejects_invalid_plate(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    result = parking_module.vehicle_entry("???")

    assert result["success"] is False
    assert result["message"] == "Invalid plate text"


def test_vehicle_entry_normalizes_and_persists_plate(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    result = parking_module.vehicle_entry("66b1\n069.99", ocr_confidence=1.7, ocr_engine="paddleocr", ocr_text="66B106999", manual_override=True)

    assert result["success"] is True
    assert result["plate_entry"] == "66-B1 069.99"

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT plate_entry, status, match_result, entry_ocr_confidence, entry_ocr_engine, entry_ocr_text, entry_manual_override FROM parking_logs WHERE ticket_id = ?", (result["ticket_id"],)).fetchone()
    conn.close()

    assert row == ("66-B1 069.99", "IN_PARKING", "PENDING", 1.0, "paddleocr", "66B106999", 1)


def test_vehicle_exit_returns_mismatch_for_different_plate(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    entry = parking_module.vehicle_entry("66B106999")
    result = parking_module.vehicle_exit(entry["ticket_id"], "67B106999")

    assert result["success"] is True
    assert result["match_result"] == "MISMATCH"


def test_vehicle_entry_rejects_duplicate_active_plate(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    first = parking_module.vehicle_entry("66B106999")
    second = parking_module.vehicle_entry("66-B1 069.99")

    assert first["success"] is True
    assert second["success"] is False
    assert second["message"] == "Vehicle already has an active ticket"
    assert second["ticket_id"] == first["ticket_id"]


def test_concurrent_entries_same_plate_create_single_ticket(tmp_path, monkeypatch):
    import threading

    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(8)

    def worker():
        barrier.wait()
        result = parking_module.vehicle_entry("66B106999")
        with lock:
            results.append(result)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    successes = [result for result in results if result.get("success")]
    assert len(successes) == 1
    assert len({result["ticket_id"] for result in successes}) == 1


def test_vehicle_exit_rejects_completed_ticket(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    entry = parking_module.vehicle_entry("66B106999")
    first_exit = parking_module.vehicle_exit(entry["ticket_id"], "66B106999")
    second_exit = parking_module.vehicle_exit(entry["ticket_id"], "66B106999")

    assert first_exit["success"] is True
    assert second_exit["success"] is False
    assert second_exit["message"] == "Vehicle already checked out"


def test_vehicle_exit_manual_override_can_resolve_to_match(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    entry = parking_module.vehicle_entry("66-B1 069.99")
    result = parking_module.vehicle_exit(entry["ticket_id"], "66b106999", ocr_engine="fast-alpr-easyocr", ocr_text="66B106999", manual_override=True)

    assert result["success"] is True
    assert result["match_result"] == "MATCH"
    assert result["plate_entry"] == "66-B1 069.99"
    assert result["plate_exit"] == "66-B1 069.99"

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT exit_ocr_engine, exit_ocr_text, exit_manual_override FROM parking_logs WHERE ticket_id = ?", (entry["ticket_id"],)).fetchone()
    conn.close()

    assert row == ("fast-alpr-easyocr", "66B106999", 1)


def test_vehicle_exit_returns_not_found_for_missing_ticket(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    result = parking_module.vehicle_exit("T404", "66B106999")

    assert result["success"] is False
    assert result["message"] == "Ticket ID not found"


def test_vehicle_can_reenter_after_checkout(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    first = parking_module.vehicle_entry("66B106999")
    exit_result = parking_module.vehicle_exit(first["ticket_id"], "66B106999")
    second = parking_module.vehicle_entry("66B106999")

    assert first["success"] is True
    assert exit_result["success"] is True
    assert second["success"] is True
    assert second["ticket_id"] != first["ticket_id"]


def test_vehicle_exit_persists_image_paths_and_clamps_confidence(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    entry = parking_module.vehicle_entry("66B106999")
    result = parking_module.vehicle_exit(
        entry["ticket_id"],
        "66B106999",
        image_path="exit.jpg",
        detected_path="detected.jpg",
        plate_path="plate.jpg",
        ocr_confidence=-0.5,
    )

    assert result["success"] is True
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT exit_image_path, exit_detected_path, exit_plate_path, exit_ocr_confidence FROM parking_logs WHERE ticket_id = ?",
        (entry["ticket_id"],),
    ).fetchone()
    conn.close()
    assert row == ("exit.jpg", "detected.jpg", "plate.jpg", 0.0)


def test_active_ticket_query_excludes_completed_tickets(tmp_path, monkeypatch):
    db_path = tmp_path / "parking.db"
    db_module.init_db(db_path)
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)
    monkeypatch.setattr(db_module, "DB_PATH", db_path)

    completed = parking_module.vehicle_entry("66B106999")
    parking_module.vehicle_exit(completed["ticket_id"], "66B106999")
    active = parking_module.vehicle_entry("67B106999")

    active_df = db_module.get_active_tickets(db_path)

    assert set(active_df["ticket_id"]) == {active["ticket_id"]}


def test_vehicle_entry_supports_legacy_plate_number_column(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE parking_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT,
            plate_number TEXT NOT NULL,
            plate_exit TEXT,
            time_in TEXT,
            time_out TEXT,
            status TEXT,
            match_result TEXT,
            plate_entry TEXT,
            entry_time TEXT,
            exit_time TEXT,
            entry_image_path TEXT,
            entry_detected_path TEXT,
            entry_plate_path TEXT,
            exit_image_path TEXT,
            exit_detected_path TEXT,
            exit_plate_path TEXT,
            ocr_confidence REAL,
            entry_ocr_confidence REAL,
            exit_ocr_confidence REAL,
            entry_ocr_engine TEXT,
            exit_ocr_engine TEXT,
            entry_ocr_text TEXT,
            exit_ocr_text TEXT,
            entry_manual_override INTEGER NOT NULL DEFAULT 0,
            exit_manual_override INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(parking_module, "DB_PATH", db_path)

    result = parking_module.vehicle_entry("66B106999")

    assert result["success"] is True
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT plate_number, plate_entry, time_in, entry_time FROM parking_logs WHERE ticket_id = ?", (result["ticket_id"],)).fetchone()
    conn.close()
    assert row[0] == "66-B1 069.99"
    assert row[1] == "66-B1 069.99"
    assert row[2]
    assert row[3]
