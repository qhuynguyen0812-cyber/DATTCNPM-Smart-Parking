from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import sqlite3

from backend import db, parking_service as parking


def test_concurrent_entry_and_exit_keep_single_ticket_and_audit_per_vehicle(tmp_path, monkeypatch):
    database = tmp_path / "concurrency.db"
    db.init_db(database)
    monkeypatch.setattr(parking, "DB_PATH", database)
    plates = [f"59-B1 {123 + i:03d}.45" for i in range(6)]
    with ThreadPoolExecutor(max_workers=12) as pool:
        entries = list(pool.map(lambda plate: parking.vehicle_entry(plate, actor="test-operator"), plates * 8))
    successes = [result for result in entries if result["success"]]
    assert len(successes) == 6
    assert Counter(result["plate_entry"] for result in successes) == Counter(plates)
    with ThreadPoolExecutor(max_workers=12) as pool:
        exits = list(pool.map(lambda row: parking.vehicle_exit(row["ticket_id"], row["plate_entry"], actor="test-operator"), successes * 6))
    assert sum(result["success"] for result in exits) == 6
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT COUNT(*) FROM parking_logs").fetchone()[0] == 6
        assert conn.execute("SELECT COUNT(*) FROM parking_logs WHERE status='COMPLETED'").fetchone()[0] == 6
        events = dict(conn.execute("SELECT event_type, COUNT(*) FROM parking_events GROUP BY event_type"))
        assert events == {"VEHICLE_ENTRY": 6, "VEHICLE_EXIT": 6}
        actions = dict(conn.execute("SELECT action, COUNT(*) FROM audit_logs GROUP BY action"))
        assert actions == {"vehicle.entry": 6, "vehicle.exit": 6}
