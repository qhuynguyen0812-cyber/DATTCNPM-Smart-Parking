import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app_service import process_plate_image
from backend.config import BENCHMARK_UPLOADS_DIR
from backend.plate_format import normalize_plate_text

DATASET_CSV = ROOT / "data" / "benchmark" / "datasets" / "benchmark_dataset.csv"


def normalize(value: str) -> str:
    return normalize_plate_text(value or "")


def resolve_benchmark_uploads_dir() -> Path:
    return Path(BENCHMARK_UPLOADS_DIR)


def iter_dataset_rows(dataset_csv: Path = DATASET_CSV):
    with dataset_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for item in reader:
            yield item


def evaluate_image(image_path: Path) -> dict:
    processed = process_plate_image(str(image_path))
    return processed.ocr
