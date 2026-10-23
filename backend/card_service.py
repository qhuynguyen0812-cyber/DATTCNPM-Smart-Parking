"""RFID Card Service for Smart Campus Parking.

Manages 13.56MHz Mifare/NFC/Napas cards, including pre-registered student/faculty
smart cards and blank RFID cards (5-card combo).
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import logging
import sqlite3
from typing import Any

from backend.config import DB_PATH

logger = logging.getLogger(__name__)

RFID_CARDS_SCHEMA = """
CREATE TABLE IF NOT EXISTS rfid_cards (
    card_uid TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    user_type TEXT NOT NULL DEFAULT 'STUDENT',
    default_plate TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rfid_cards_user_type ON rfid_cards(user_type);
"""

DEFAULT_SEED_CARDS = [
    {
        "card_uid": "UTH_SV_2026_01",
        "label": "Thẻ SV UTH - Nguyễn Quang Huy",
        "user_type": "STUDENT",
        "default_plate": "59X3-123.45",
        "note": "Thẻ sinh viên Napas Contactless 13.56MHz",
    },
    {
        "card_uid": "UTH_STAFF_GV_01",
        "label": "Thẻ Cán bộ / Giảng viên CNTT",
        "user_type": "STAFF",
        "default_plate": "51F-888.88",
        "note": "Miễn phí vé 0đ - Phân luồng Khu E Tầng dưới",
    },
    {
        "card_uid": "CARD_WHITE_01",
        "label": "Thẻ Trắng #1 (Sinh viên)",
        "user_type": "STUDENT",
        "default_plate": "59X3-123.45",
        "note": "Combo 5 thẻ 13.56MHz (Quẹt để cập nhật UID thật)",
    },
    {
        "card_uid": "CARD_WHITE_02",
        "label": "Thẻ Trắng #2 (Cán bộ - Giảng viên)",
        "user_type": "STAFF",
        "default_plate": "51F-888.88",
        "note": "Combo 5 thẻ 13.56MHz (Quẹt để cập nhật UID thật)",
    },
    {
        "card_uid": "CARD_WHITE_03",
        "label": "Thẻ Trắng #3 (Khách vãng lai)",
        "user_type": "GUEST",
        "default_plate": "50A-999.99",
        "note": "Vé lượt khách liên hệ công tác",
    },
    {
        "card_uid": "CARD_WHITE_04",
        "label": "Thẻ Trắng #4 (Vé lượt sinh viên)",
        "user_type": "STUDENT",
        "default_plate": "59B1-678.90",
        "note": "Vé lượt sinh viên tự do",
    },
    {
        "card_uid": "CARD_WHITE_05",
        "label": "Thẻ Trắng #5 (Dự phòng)",
        "user_type": "STUDENT",
        "default_plate": "72A-111.22",
        "note": "Thẻ dự phòng phát sinh",
    },
]


def _connect(db_path: Any | None = None) -> sqlite3.Connection:
    target = db_path if db_path is not None else DB_PATH
    return sqlite3.connect(target)


def ensure_rfid_cards_table(db_path: Any | None = None) -> None:
    """Ensure the rfid_cards table exists and seed initial default cards."""
    with _connect(db_path) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.executescript(RFID_CARDS_SCHEMA)
            cursor.execute("SELECT COUNT(*) FROM rfid_cards")
            count = cursor.fetchone()[0]
            if count == 0:
                for c in DEFAULT_SEED_CARDS:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO rfid_cards (card_uid, label, user_type, default_plate, is_active, note)
                        VALUES (?, ?, ?, ?, 1, ?)
                        """,
                        (c["card_uid"], c["label"], c["user_type"], c["default_plate"], c["note"]),
                    )
        conn.commit()


def list_cards(db_path: Any | None = None) -> list[dict[str, Any]]:
    """List all registered RFID cards."""
    ensure_rfid_cards_table(db_path)
    with _connect(db_path) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                SELECT card_uid, label, user_type, default_plate, is_active, note, created_at, updated_at
                FROM rfid_cards
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "card_uid": r[0],
                    "label": r[1],
                    "user_type": r[2],
                    "default_plate": r[3],
                    "is_active": bool(r[4]),
                    "note": r[5],
                    "created_at": r[6],
                    "updated_at": r[7],
                }
                for r in rows
            ]


def get_card(card_uid: str, db_path: Any | None = None) -> dict[str, Any] | None:
    """Get card by UID (case-insensitive)."""
    if not card_uid:
        return None
    ensure_rfid_cards_table(db_path)
    clean_uid = card_uid.strip().upper()
    with _connect(db_path) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                SELECT card_uid, label, user_type, default_plate, is_active, note, created_at, updated_at
                FROM rfid_cards
                WHERE UPPER(card_uid) = ?
                """,
                (clean_uid,),
            )
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "card_uid": r[0],
                "label": r[1],
                "user_type": r[2],
                "default_plate": r[3],
                "is_active": bool(r[4]),
                "note": r[5],
                "created_at": r[6],
                "updated_at": r[7],
            }


def save_card(
    card_uid: str,
    label: str,
    user_type: str = "STUDENT",
    default_plate: str | None = None,
    is_active: bool = True,
    note: str | None = None,
    db_path: Any | None = None,
) -> dict[str, Any]:
    """Register or update an RFID card."""
    clean_uid = (card_uid or "").strip().upper()
    if not clean_uid:
        raise ValueError("card_uid is required")
    clean_label = (label or clean_uid).strip()
    clean_user_type = (user_type or "STUDENT").strip().upper()
    if clean_user_type not in ("STUDENT", "STAFF", "GUEST"):
        clean_user_type = "STUDENT"
    clean_plate = (default_plate or "").strip() or None
    clean_note = (note or "").strip() or None
    now_str = datetime.now(timezone.utc).isoformat()

    ensure_rfid_cards_table(db_path)
    with _connect(db_path) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO rfid_cards (card_uid, label, user_type, default_plate, is_active, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_uid) DO UPDATE SET
                    label = excluded.label,
                    user_type = excluded.user_type,
                    default_plate = excluded.default_plate,
                    is_active = excluded.is_active,
                    note = excluded.note,
                    updated_at = excluded.updated_at
                """,
                (clean_uid, clean_label, clean_user_type, clean_plate, 1 if is_active else 0, clean_note, now_str, now_str),
            )
        conn.commit()

    return {
        "success": True,
        "card_uid": clean_uid,
        "label": clean_label,
        "user_type": clean_user_type,
        "default_plate": clean_plate,
        "is_active": is_active,
        "note": clean_note,
        "updated_at": now_str,
    }


def delete_card(card_uid: str, db_path: Any | None = None) -> bool:
    """Delete a card from the registry."""
    if not card_uid:
        return False
    ensure_rfid_cards_table(db_path)
    clean_uid = card_uid.strip().upper()
    with _connect(db_path) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("DELETE FROM rfid_cards WHERE UPPER(card_uid) = ?", (clean_uid,))
            deleted = cursor.rowcount > 0
        conn.commit()
    return deleted


def assign_blank_slot(slot_number: int, real_card_uid: str, db_path: Any | None = None) -> dict[str, Any]:
    """Assign physical card UID to one of the 5 white card slots (slot 1 to 5)."""
    if not (1 <= slot_number <= 5):
        raise ValueError("Slot number must be between 1 and 5")
    slot_id = f"CARD_WHITE_{slot_number:02d}"
    clean_new_uid = real_card_uid.strip().upper()
    if not clean_new_uid:
        raise ValueError("real_card_uid cannot be empty")

    ensure_rfid_cards_table(db_path)
    existing_slot = get_card(slot_id, db_path=db_path)

    label = f"Thẻ Trắng #{slot_number}"
    user_type = "STUDENT"
    default_plate = None
    note = f"Đã gán với thẻ vật lý UID {clean_new_uid}"

    if existing_slot:
        label = existing_slot.get("label") or label
        user_type = existing_slot.get("user_type") or user_type
        default_plate = existing_slot.get("default_plate")
        # remove old placeholder row if UID changed
        delete_card(slot_id, db_path=db_path)

    return save_card(
        card_uid=clean_new_uid,
        label=label,
        user_type=user_type,
        default_plate=default_plate,
        is_active=True,
        note=note,
        db_path=db_path,
    )
