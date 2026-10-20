import pytest
from datetime import datetime, timedelta
from pathlib import Path

from backend.config import (
    DEFAULT_PARKING_FEE,
    OVERNIGHT_SURCHARGE,
    VIETQR_ACCOUNT_NO,
    VIETQR_BANK_ID,
)
from backend.db import (
    apply_migrations,
    fetch_active_ticket_by_card_id,
    fetch_ticket_by_card_id,
    get_all_zones,
    get_zone_status,
    recalculate_zone_occupancies,
    update_zone_occupancy,
)
from backend.parking_service import (
    ACTIVE_STATUS,
    COMPLETED_STATUS,
    calculate_parking_fee,
    vehicle_entry,
    vehicle_exit,
)
from backend.vietqr_service import build_parking_vietqr, build_vietqr_url


def test_campus_zones_initialization(tmp_path):
    test_db = tmp_path / "test_zones.db"
    apply_migrations(test_db)

    zones = get_all_zones(test_db)
    zone_ids = [z["zone_id"] for z in zones]
    assert "ZONE_A" in zone_ids
    assert "ZONE_B" in zone_ids
    assert "ZONE_C" in zone_ids
    assert "ZONE_E" in zone_ids

    status_a = get_zone_status("ZONE_A", test_db)
    assert status_a is not None
    assert status_a["max_capacity"] == 250
    assert status_a["current_occupied"] == 0
    assert status_a["available_slots"] == 250
    assert not status_a["is_full"]


def test_campus_zone_occupancy_update(tmp_path):
    test_db = tmp_path / "test_zones_update.db"
    apply_migrations(test_db)

    assert update_zone_occupancy("ZONE_B", delta=10, db_path=test_db)
    status_b = get_zone_status("ZONE_B", test_db)
    assert status_b["current_occupied"] == 10
    assert status_b["available_slots"] == 440

    # Decrement
    assert update_zone_occupancy("ZONE_B", delta=-5, db_path=test_db)
    status_b = get_zone_status("ZONE_B", test_db)
    assert status_b["current_occupied"] == 5

    # Should not go below 0
    assert update_zone_occupancy("ZONE_B", delta=-20, db_path=test_db)
    status_b = get_zone_status("ZONE_B", test_db)
    assert status_b["current_occupied"] == 0


def test_vietqr_url_and_payload_generation():
    url = build_vietqr_url(5000, "GUIXE RFID_001")
    assert f"https://img.vietqr.io/image/{VIETQR_BANK_ID}-{VIETQR_ACCOUNT_NO}" in url
    assert "amount=5000" in url
    assert "GUIXE+RFID_001" in url or "GUIXE%20RFID_001" in url

    payload = build_parking_vietqr(card_id="RFID_999", amount=10000, ticket_id="T202610200001")
    assert payload["amount"] == 10000
    assert payload["memo"] == "GUIXE RFID_999"
    assert "qr_image_url" in payload


def test_calculate_parking_fee_same_day():
    entry_time = "2026-10-20 08:30:00"
    exit_time = "2026-10-20 17:15:00"

    tariff = calculate_parking_fee(entry_time, exit_time)
    assert tariff["base_fee"] == DEFAULT_PARKING_FEE
    assert tariff["overnight_surcharge"] == 0
    assert tariff["total_fee"] == DEFAULT_PARKING_FEE
    assert not tariff["is_overnight"]


def test_calculate_parking_fee_overnight_past_23h():
    entry_time = "2026-10-20 19:00:00"
    exit_time = "2026-10-20 23:30:00"  # past 23:00

    tariff = calculate_parking_fee(entry_time, exit_time)
    assert tariff["base_fee"] == DEFAULT_PARKING_FEE
    assert tariff["overnight_surcharge"] == OVERNIGHT_SURCHARGE
    assert tariff["total_fee"] == DEFAULT_PARKING_FEE + OVERNIGHT_SURCHARGE
    assert tariff["is_overnight"]


def test_calculate_parking_fee_next_day():
    entry_time = "2026-10-20 14:00:00"
    exit_time = "2026-10-21 07:00:00"  # next day

    tariff = calculate_parking_fee(entry_time, exit_time)
    assert tariff["overnight_surcharge"] == OVERNIGHT_SURCHARGE
    assert tariff["total_fee"] == DEFAULT_PARKING_FEE + OVERNIGHT_SURCHARGE
    assert tariff["is_overnight"]


def test_vehicle_entry_exit_lifecycle_with_rfid_and_zones(tmp_path, monkeypatch):
    test_db = tmp_path / "test_lifecycle.db"
    apply_migrations(test_db)
    monkeypatch.setattr("backend.parking_service.DB_PATH", test_db)
    monkeypatch.setattr("backend.db.DB_PATH", test_db)

    # 1. Entry with Card ID and Zone assignment
    entry_res = vehicle_entry(
        plate_text="59X3-12345",
        card_id="CARD_UTH_001",
        gate_entry="GATE_1",
        lane_entry="LANE_1",
        zone_assigned="ZONE_E",
    )
    assert entry_res["success"] is True
    ticket_id = entry_res["ticket_id"]
    assert entry_res["card_id"] == "CARD_UTH_001"
    assert entry_res["zone_assigned"] == "ZONE_E"
    assert entry_res["fee"] == DEFAULT_PARKING_FEE

    # Zone E occupancy should be 1
    zone_e = get_zone_status("ZONE_E", test_db)
    assert zone_e["current_occupied"] == 1

    # 2. Prevent duplicate entry with same card ID while active
    dup_res = vehicle_entry(
        plate_text="59X3-99999",
        card_id="CARD_UTH_001",
        gate_entry="GATE_1",
        lane_entry="LANE_2",
        zone_assigned="ZONE_A",
    )
    assert dup_res["success"] is False
    assert "already in use" in dup_res["message"]

    # 3. Card lookup
    active_by_card = fetch_active_ticket_by_card_id("CARD_UTH_001", test_db)
    assert active_by_card is not None
    assert active_by_card["ticket_id"] == ticket_id

    # 4. Vehicle Exit using Card ID (without passing ticket_id directly) and VietQR
    exit_res = vehicle_exit(
        card_id="CARD_UTH_001",
        plate_text="59X3-12345",
        gate_exit="GATE_3",
        lane_exit="LANE_1",
        payment_method="VIETQR",
    )
    assert exit_res["success"] is True
    assert exit_res["ticket_id"] == ticket_id
    assert exit_res["status"] == COMPLETED_STATUS
    assert exit_res["vietqr"] is not None
    assert exit_res["vietqr"]["memo"] == "GUIXE CARD_UTH_001"
    assert exit_res["fee"] == DEFAULT_PARKING_FEE

    # Zone E occupancy should decrement back to 0
    zone_e_after = get_zone_status("ZONE_E", test_db)
    assert zone_e_after["current_occupied"] == 0


def test_recalculate_zone_occupancies(tmp_path, monkeypatch):
    test_db = tmp_path / "test_recalc.db"
    apply_migrations(test_db)
    monkeypatch.setattr("backend.parking_service.DB_PATH", test_db)
    monkeypatch.setattr("backend.db.DB_PATH", test_db)

    # Add 2 vehicles in ZONE_A and 1 in ZONE_C
    vehicle_entry("59X1-11111", card_id="C1", zone_assigned="ZONE_A")
    vehicle_entry("59X1-22222", card_id="C2", zone_assigned="ZONE_A")
    vehicle_entry("59X1-33333", card_id="C3", zone_assigned="ZONE_C")

    counts = recalculate_zone_occupancies(test_db)
    assert counts.get("ZONE_A") == 2
    assert counts.get("ZONE_C") == 1

    status_a = get_zone_status("ZONE_A", test_db)
    status_c = get_zone_status("ZONE_C", test_db)
    assert status_a["current_occupied"] == 2
    assert status_c["current_occupied"] == 1
