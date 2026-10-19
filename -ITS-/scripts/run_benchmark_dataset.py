import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr
from backend.plate_format import normalize_plate_text


UPLOADS_DIR = Path(r"C:\Users\huy81\plate_demo_data\uploads")
DATASET_CSV = ROOT / "benchmark_dataset.csv"
RESULTS_CSV = ROOT / "benchmark_dataset_results.csv"
SUMMARY_TXT = ROOT / "benchmark_dataset_summary.txt"


def normalize(value: str) -> str:
    return normalize_plate_text(value or "")


def main():
    rows = []
    counters = Counter()

    with DATASET_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for item in reader:
            file_name = (item.get("file") or "").strip()
            expected_plate = (item.get("expected_plate") or "").strip()
            label = (item.get("label") or "unknown").strip().lower()
            notes = (item.get("notes") or "").strip()
            image_path = UPLOADS_DIR / file_name

            if not image_path.exists():
                result_row = {
                    "file": file_name,
                    "label": label,
                    "expected_plate": expected_plate,
                    "predicted_plate": "",
                    "confidence": 0.0,
                    "is_usable": False,
                    "exact_match": False,
                    "quality_note": "missing file",
                    "notes": notes,
                }
                rows.append(result_row)
                counters[f"{label}_missing"] += 1
                continue

            result = run_alpr(str(image_path))
            predicted_plate = result.get("text", "")
            is_usable = bool(result.get("is_usable", False))
            exact_match = normalize(predicted_plate) == normalize(expected_plate) if expected_plate else False

            result_row = {
                "file": file_name,
                "label": label,
                "expected_plate": expected_plate,
                "predicted_plate": predicted_plate,
                "confidence": result.get("confidence", 0.0),
                "is_usable": is_usable,
                "exact_match": exact_match,
                "quality_note": result.get("quality_note", ""),
                "notes": notes,
            }
            rows.append(result_row)

            counters[f"{label}_total"] += 1
            if is_usable:
                counters[f"{label}_usable"] += 1
            if exact_match:
                counters[f"{label}_exact"] += 1

    with RESULTS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "label", "expected_plate", "predicted_plate", "confidence", "is_usable", "exact_match", "quality_note", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    summary_lines = []
    for label in ["good", "medium", "bad"]:
        total = counters.get(f"{label}_total", 0)
        usable = counters.get(f"{label}_usable", 0)
        exact = counters.get(f"{label}_exact", 0)
        if total:
            summary_lines.append(f"{label}: total={total}, usable={usable}, exact={exact}")
    summary_lines.append(f"results_csv={RESULTS_CSV}")
    SUMMARY_TXT.write_text("\n".join(summary_lines), encoding="utf-8")
    print("done")
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
