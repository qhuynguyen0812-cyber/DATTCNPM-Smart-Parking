import csv
import os
import sys
from pathlib import Path

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr
from backend.paddle_ocr_adapter import run_paddleocr
from backend.plate_format import normalize_plate_text

UPLOADS_DIR = Path(r"C:\Users\huy81\plate_demo_data\uploads")
DATASET_CSV = ROOT / "benchmark_dataset.csv"
RESULTS_CSV = ROOT / "ocr_engine_comparison.csv"


def normalize(value: str) -> str:
    return normalize_plate_text(value or "")


def main():
    rows = []
    with DATASET_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for item in reader:
            file_name = (item.get("file") or "").strip()
            expected_plate = (item.get("expected_plate") or "").strip()
            label = (item.get("label") or "unknown").strip().lower()
            image_path = UPLOADS_DIR / file_name
            if not image_path.exists():
                continue

            easy = run_alpr(str(image_path))
            paddle = run_paddleocr(str(image_path))

            rows.append(
                {
                    "file": file_name,
                    "label": label,
                    "expected_plate": expected_plate,
                    "easy_text": easy.get("text", ""),
                    "easy_confidence": easy.get("confidence", 0.0),
                    "easy_usable": easy.get("is_usable", False),
                    "easy_exact": normalize(easy.get("text", "")) == normalize(expected_plate) if expected_plate else False,
                    "paddle_text": paddle.get("text", ""),
                    "paddle_confidence": paddle.get("confidence", 0.0),
                    "paddle_usable": paddle.get("is_usable", False),
                    "paddle_exact": normalize(paddle.get("text", "")) == normalize(expected_plate) if expected_plate else False,
                }
            )

    with RESULTS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "label",
                "expected_plate",
                "easy_text",
                "easy_confidence",
                "easy_usable",
                "easy_exact",
                "paddle_text",
                "paddle_confidence",
                "paddle_usable",
                "paddle_exact",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(RESULTS_CSV)
    print(f"count={len(rows)}")


if __name__ == "__main__":
    main()
