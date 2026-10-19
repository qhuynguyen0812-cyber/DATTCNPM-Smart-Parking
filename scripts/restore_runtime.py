from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from zipfile import ZipFile

from backend.config import BASE_DIR, DB_PATH, UPLOAD_DIR


def _validate_db_readable(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    finally:
        conn.close()


def _write_member(archive: ZipFile, member: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(member) as source, open(target, "wb") as destination:
        destination.write(source.read())


def validate_backup_archive(archive_path: Path) -> list[str]:
    if not archive_path.exists():
        raise FileNotFoundError(f"Backup archive not found: {archive_path}")
    with ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
    if "manifest.json" not in names:
        raise ValueError("Not a valid ITS backup: missing manifest.json")
    return names


def restore_runtime_backup(
    archive_path: Path,
    *,
    base_dir: Path = BASE_DIR,
    db_path: Path = DB_PATH,
    uploads_dir: Path = UPLOAD_DIR,
    dry_run: bool = False,
) -> dict:
    """Restore a runtime backup produced by scripts/backup_runtime.py.

    Overwrites the current database and uploads with the archived copies.
    """
    names = validate_backup_archive(archive_path)
    base_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    result = {"db_restored": False, "uploads_restored": 0}

    with ZipFile(archive_path, "r") as archive:
        db_arcname = f"runtime/{db_path.name}"
        if db_arcname in names:
            result["db_restored"] = True
            if not dry_run:
                _write_member(archive, db_arcname, db_path)

        uploads_prefix = "runtime/uploads/"
        upload_members = [n for n in names if n.startswith(uploads_prefix) and not n.endswith("/")]
        result["uploads_restored"] = len(upload_members)
        if not dry_run:
            for member in upload_members:
                relative = member[len(uploads_prefix):]
                _write_member(archive, member, uploads_dir / relative)

    if result["db_restored"] and not dry_run and db_path.exists():
        _validate_db_readable(db_path)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore an ITS runtime backup (overwrites current DB and uploads).")
    parser.add_argument("backup", help="Path to a backup .zip produced by scripts/backup_runtime.py")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview without writing files")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    args = parser.parse_args()

    archive_path = Path(args.backup)
    if not args.dry_run and not args.yes:
        answer = input(f"Restore will OVERWRITE current database and uploads from {archive_path}. Type 'yes' to continue: ")
        if answer.strip().lower() != "yes":
            print("Aborted.")
            return 1

    result = restore_runtime_backup(archive_path, dry_run=args.dry_run)
    print(f"Restore complete: db_restored={result['db_restored']} uploads_restored={result['uploads_restored']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
