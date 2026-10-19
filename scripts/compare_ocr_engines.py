import csv
import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr
from backend.config import ENABLE_PADDLE_OCR, REPORT_DIR
from backend.paddle_ocr_adapter import run_paddleocr
from scripts.benchmark_common import DATASET_CSV, iter_dataset_rows, resolve_benchmark_uploads_dir
from backend.plate_format import normalize_plate_text

RESULTS_CSV = REPORT_DIR / "ocr_engine_comparison.csv"
SUMMARY_TXT = REPORT_DIR / "ocr_engine_comparison_summary.txt"
UPLOADS_DIR = resolve_benchmark_uploads_dir()


def normalize(value: str) -> str:
    return normalize_plate_text(value or "")


def evaluate_result(engine_name: str, result: dict, expected_plate: str, counters: Counter):
    predicted = result.get("text", "")
    usable = bool(result.get("is_usable", False))
    exact = normalize(predicted) == normalize(expected_plate) if expected_plate else False
    counters[f"{engine_name}_total"] += 1
    if usable:
        counters[f"{engine_name}_usable"] += 1
    if exact:
        counters[f"{engine_name}_exact"] += 1
    return predicted, usable, exact


def main():
    rows = []
    counters = Counter()

    if not DATASET_CSV.exists():
        raise SystemExit(f"Missing dataset file: {DATASET_CSV}")

    for item in iter_dataset_rows(DATASET_CSV):
        file_name = (item.get("file") or "").strip()
        expected_plate = (item.get("expected_plate") or "").strip()
        label = (item.get("label") or "unknown").strip().lower()
        image_path = UPLOADS_DIR / file_name
        if not image_path.exists():
            continue

        easy = run_alpr(str(image_path))
        easy_text, easy_usable, easy_exact = evaluate_result("easy", easy, expected_plate, counters)

        paddle = {"text": "", "confidence": 0.0, "is_usable": False, "quality_note": "PaddleOCR disabled"}
        if ENABLE_PADDLE_OCR:
            paddle = run_paddleocr(str(image_path))
        paddle_text, paddle_usable, paddle_exact = evaluate_result("paddle", paddle, expected_plate, counters)

        rows.append(
            {
                    "file": file_name,
                    "label": label,
                    "expected_plate": expected_plate,
                    "easy_text": easy_text,
                    "easy_confidence": easy.get("confidence", 0.0),
                    "easy_usable": easy_usable,
                    "easy_exact": easy_exact,
                    "easy_quality_note": easy.get("quality_note", ""),
                    "paddle_text": paddle_text,
                    "paddle_confidence": paddle.get("confidence", 0.0),
                    "paddle_usable": paddle_usable,
                    "paddle_exact": paddle_exact,
                    "paddle_quality_note": paddle.get("quality_note", ""),
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
                "easy_quality_note",
                "paddle_text",
                "paddle_confidence",
                "paddle_usable",
                "paddle_exact",
                "paddle_quality_note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary_lines = [
        f"dataset_count={len(rows)}",
        f"easy_total={counters.get('easy_total', 0)}",
        f"easy_usable={counters.get('easy_usable', 0)}",
        f"easy_exact={counters.get('easy_exact', 0)}",
        f"paddle_total={counters.get('paddle_total', 0)}",
        f"paddle_usable={counters.get('paddle_usable', 0)}",
        f"paddle_exact={counters.get('paddle_exact', 0)}",
        f"paddle_enabled={ENABLE_PADDLE_OCR}",
        "benchmark_target=run_alpr (engine comparison only)",
        f"uploads_dir={UPLOADS_DIR}",
        f"results_csv={RESULTS_CSV}",
    ]
    SUMMARY_TXT.write_text("\n".join(summary_lines), encoding="utf-8")

    print(RESULTS_CSV)
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
