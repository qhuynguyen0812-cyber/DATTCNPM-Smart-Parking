from pathlib import Path
import json
import sqlite3
import sys
from zipfile import ZipFile

import pytest

pytestmark = pytest.mark.integration


from scripts.backup_runtime import create_runtime_backup


def test_create_runtime_backup_includes_db_uploads_and_manifest(tmp_path):
    db_path = tmp_path / "parking_system.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    (uploads_dir / "sample.txt").write_text("hello", encoding="utf-8")

    out_zip = tmp_path / "backup.zip"
    result = create_runtime_backup(out_zip, db_path=db_path, uploads_dir=uploads_dir)

    assert result == out_zip
    assert out_zip.exists()

    with ZipFile(out_zip, "r") as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "runtime/parking_system.db" in names
        assert "runtime/uploads/sample.txt" in names

        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["db_exists"] is True
        assert manifest["upload_file_count"] == 1
