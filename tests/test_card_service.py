from pathlib import Path
import pytest
from backend.card_service import (
    ensure_rfid_cards_table,
    list_cards,
    get_card,
    save_card,
    delete_card,
    assign_blank_slot,
)
from backend.parking_service import vehicle_entry, vehicle_exit


def test_card_service_crud(tmp_path):
    db_file = tmp_path / "test_cards.db"
    ensure_rfid_cards_table(db_file)

    cards = list_cards(db_file)
    assert len(cards) >= 5
    uids = {c["card_uid"] for c in cards}
    assert "UTH_SV_2026_01" in uids
    assert "UTH_STAFF_GV_01" in uids

    # Save a custom card
    res = save_card("TEST_UID_99", "Thẻ Test Sinh Viên", "STUDENT", "59X3-999.99", db_path=db_file)
    assert res["success"] is True

    card = get_card("test_uid_99", db_file)
    assert card is not None
    assert card["label"] == "Thẻ Test Sinh Viên"
    assert card["default_plate"] == "59X3-999.99"

    # Delete card
    deleted = delete_card("TEST_UID_99", db_file)
    assert deleted is True
    assert get_card("TEST_UID_99", db_file) is None


def test_assign_blank_slot(tmp_path):
    db_file = tmp_path / "test_slots.db"
    ensure_rfid_cards_table(db_file)

    # Assign physical card UID '0849201948' to slot 1
    res = assign_blank_slot(1, "0849201948", db_path=db_file)
    assert res["card_uid"] == "0849201948"
    assert res["user_type"] == "STUDENT"

    card = get_card("0849201948", db_file)
    assert card is not None
    assert card["label"] == "Thẻ Trắng #1 (Sinh viên)"
