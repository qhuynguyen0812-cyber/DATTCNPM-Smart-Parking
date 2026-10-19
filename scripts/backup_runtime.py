from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from backend.config import BASE_DIR, DB_PATH, UPLOAD_DIR

BACKUP_ROOT = BASE_DIR / "backups"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _validate_db_readable(db_path: Path) -> None:
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    finally:
        conn.close()


def build_backup_manifest(db_path: Path, uploads_dir: Path) -> dict:
    upload_files = sorted([p for p in uploads_dir.rglob("*") if p.is_file()]) if uploads_dir.exists() else []
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_dir": str(BASE_DIR),
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "uploads_dir": str(uploads_dir),
        "upload_file_count": len(upload_files),
    }


def create_runtime_backup(output_path: Path | None = None, *, db_path: Path = DB_PATH, uploads_dir: Path = UPLOAD_DIR) -> Path:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    target = output_path or (BACKUP_ROOT / f"its-runtime-backup-{_timestamp()}.zip")
    target = _ensure_parent(target)

    _validate_db_readable(db_path)
    manifest = build_backup_manifest(db_path, uploads_dir)

    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        if db_path.exists():
            archive.write(db_path, arcname=f"runtime/{db_path.name}")
        if uploads_dir.exists():
            for file_path in uploads_dir.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, arcname=str(Path("runtime/uploads") / file_path.relative_to(uploads_dir)))
    return target


def main() -> None:
    backup_path = create_runtime_backup()
    print(f"Created runtime backup: {backup_path}")


if __name__ == "__main__":
    main()
