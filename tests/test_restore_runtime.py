from pathlib import Path
import sqlite3

import pytest

pytestmark = pytest.mark.integration


from scripts.backup_runtime import create_runtime_backup
from scripts.restore_runtime import restore_runtime_backup, validate_backup_archive


def test_restore_runtime_backup_roundtrip(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    db_path = source_dir / "parking_system.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO sample(id) VALUES (1)")
    conn.commit()
    conn.close()

    uploads_dir = source_dir / "uploads"
    uploads_dir.mkdir()
    (uploads_dir / "entry_1.jpg").write_text("img", encoding="utf-8")

    backup_zip = tmp_path / "backup.zip"
    create_runtime_backup(backup_zip, db_path=db_path, uploads_dir=uploads_dir)

    target_dir = tmp_path / "target"
    target_dir.mkdir()
    target_db = target_dir / "parking_system.db"
    target_uploads = target_dir / "uploads"

    result = restore_runtime_backup(
        backup_zip,
        base_dir=target_dir,
        db_path=target_db,
        uploads_dir=target_uploads,
    )

    assert result["db_restored"] is True
    assert result["uploads_restored"] == 1
    assert target_db.exists()
    assert (target_uploads / "entry_1.jpg").exists()

    conn = sqlite3.connect(target_db)
    rows = conn.execute("SELECT id FROM sample").fetchall()
    conn.close()
    assert rows == [(1,)]


def test_validate_backup_archive_rejects_missing_manifest(tmp_path):
    bad_zip = tmp_path / "bad.zip"
    import zipfile
    with zipfile.ZipFile(bad_zip, "w") as archive:
        archive.writestr("somefile.txt", "x")

    with pytest.raises(ValueError, match="manifest.json"):
        validate_backup_archive(bad_zip)
