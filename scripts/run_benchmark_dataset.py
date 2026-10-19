import csv
from collections import Counter

from scripts.benchmark_common import DATASET_CSV, ROOT, evaluate_image, iter_dataset_rows, normalize, resolve_benchmark_uploads_dir


UPLOADS_DIR = resolve_benchmark_uploads_dir()
RESULTS_CSV = ROOT / "data" / "benchmark" / "results" / "benchmark_dataset_results.csv"
SUMMARY_TXT = ROOT / "data" / "benchmark" / "results" / "benchmark_dataset_summary.txt"


def main():
    rows = []
    counters = Counter()

    for item in iter_dataset_rows(DATASET_CSV):
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

        result = evaluate_image(image_path)
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
    summary_lines.append("benchmark_target=process_plate_image")
    summary_lines.append(f"uploads_dir={UPLOADS_DIR}")
    summary_lines.append(f"results_csv={RESULTS_CSV}")
    SUMMARY_TXT.write_text("\n".join(summary_lines), encoding="utf-8")
    print("done")
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
