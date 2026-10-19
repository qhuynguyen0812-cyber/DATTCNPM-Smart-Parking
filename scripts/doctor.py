from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import BASE_DIR, BENCHMARK_UPLOADS_DIR, DB_PATH, LOG_DIR, REPORT_DIR, UPLOAD_DIR


REQUIRED_PATHS = {
    "base_dir": BASE_DIR,
    "upload_dir": UPLOAD_DIR,
    "log_dir": LOG_DIR,
    "report_dir": REPORT_DIR,
    "benchmark_uploads_dir": BENCHMARK_UPLOADS_DIR,
}


OPTIONAL_FILES = {
    "db_file": DB_PATH,
    "benchmark_dataset": ROOT / "data" / "benchmark" / "datasets" / "benchmark_dataset.csv",
    "web_entry": ROOT / "frontend" / "web" / "index.html",
    "api_entry": ROOT / "api" / "main.py",
}


def main():
    print("ITS doctor report")
    print("=" * 40)

    for name, path in REQUIRED_PATHS.items():
        status = "OK" if Path(path).exists() else "MISSING"
        print(f"[{status}] {name}: {path}")

    for name, path in OPTIONAL_FILES.items():
        status = "OK" if Path(path).exists() else "WARN"
        print(f"[{status}] {name}: {path}")


if __name__ == "__main__":
    main()
