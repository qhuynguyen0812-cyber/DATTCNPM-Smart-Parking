import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import ENABLE_OPENAI_VISION, OPENAI_BASE_URL, OPENAI_VISION_MODEL
from backend.openai_vision_adapter import run_openai_vision
from backend.plate_format import normalize_plate_text
from scripts.benchmark_common import DATASET_CSV, iter_dataset_rows, resolve_benchmark_uploads_dir

RESULTS_CSV = ROOT / "data" / "benchmark" / "results" / "benchmark_openai_vision_results.csv"
SUMMARY_TXT = ROOT / "data" / "benchmark" / "results" / "benchmark_openai_vision_summary.txt"
UPLOADS_DIR = resolve_benchmark_uploads_dir()


def normalize(value: str) -> str:
    return normalize_plate_text(value or "")


def main():
    if not ENABLE_OPENAI_VISION:
        raise SystemExit("ITS_ENABLE_OPENAI_VISION is disabled")

    if not DATASET_CSV.exists():
        raise SystemExit(f"Missing dataset file: {DATASET_CSV}")

    rows = []
    counters = Counter()

    for item in iter_dataset_rows(DATASET_CSV):
        file_name = (item.get("file") or "").strip()
        expected_plate = (item.get("expected_plate") or "").strip()
        label = (item.get("label") or "unknown").strip().lower()
        notes = (item.get("notes") or "").strip()
        image_path = UPLOADS_DIR / file_name

        if not image_path.exists():
            rows.append(
                {
                    "file": file_name,
                    "label": label,
                    "expected_plate": expected_plate,
                    "predicted_plate": "",
                    "raw_text": "",
                    "confidence": 0.0,
                    "is_usable": False,
                    "exact_match": False,
                    "quality_note": "missing file",
                    "notes": notes,
                }
            )
            counters[f"{label}_missing"] += 1
            continue

        result = run_openai_vision(str(image_path))
        predicted_plate = result.get("text", "")
        is_usable = bool(result.get("is_usable", False))
        exact_match = normalize(predicted_plate) == normalize(expected_plate) if expected_plate else False

        rows.append(
            {
                "file": file_name,
                "label": label,
                "expected_plate": expected_plate,
                "predicted_plate": predicted_plate,
                "raw_text": result.get("raw_text", ""),
                "confidence": result.get("confidence", 0.0),
                "is_usable": is_usable,
                "exact_match": exact_match,
                "quality_note": result.get("quality_note", ""),
                "notes": notes,
            }
        )

        counters[f"{label}_total"] += 1
        if is_usable:
            counters[f"{label}_usable"] += 1
        if exact_match:
            counters[f"{label}_exact"] += 1

    with RESULTS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "label",
                "expected_plate",
                "predicted_plate",
                "raw_text",
                "confidence",
                "is_usable",
                "exact_match",
                "quality_note",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary_lines = []
    for label in ["good", "medium", "bad"]:
        total = counters.get(f"{label}_total", 0)
        usable = counters.get(f"{label}_usable", 0)
        exact = counters.get(f"{label}_exact", 0)
        if total:
            summary_lines.append(f"{label}: total={total}, usable={usable}, exact={exact}")
    summary_lines.extend(
        [
            "benchmark_target=run_openai_vision",
            f"openai_enabled={ENABLE_OPENAI_VISION}",
            f"openai_base_url={OPENAI_BASE_URL}",
            f"openai_model={OPENAI_VISION_MODEL}",
            f"uploads_dir={UPLOADS_DIR}",
            f"results_csv={RESULTS_CSV}",
        ]
    )
    SUMMARY_TXT.write_text("\n".join(summary_lines), encoding="utf-8")

    print(RESULTS_CSV)
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
