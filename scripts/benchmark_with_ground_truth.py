import csv

from backend.alpr_service import run_alpr
from scripts.benchmark_common import ROOT, normalize, resolve_benchmark_uploads_dir


UPLOADS_DIR = resolve_benchmark_uploads_dir()
TRUTH_CSV = ROOT / "data" / "benchmark" / "ground_truth" / "benchmark_dataset_ground_truth_template.csv"
OUT_CSV = ROOT / "data" / "benchmark" / "results" / "benchmark_ground_truth_results.csv"


def main():
    truth_csv = TRUTH_CSV
    out_csv = OUT_CSV
    rows = []
    with truth_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_name = (row.get("file") or "").strip()
            expected_plate = (row.get("expected_plate") or "").strip()
            notes = (row.get("notes") or "").strip()
            image_path = UPLOADS_DIR / file_name
            if not image_path.exists():
                rows.append({
                    "file": file_name,
                    "expected_plate": expected_plate,
                    "predicted_plate": "",
                    "confidence": 0.0,
                    "is_usable": False,
                    "exact_match": False,
                    "quality_note": "missing file",
                    "notes": notes,
                })
                continue

            result = run_alpr(str(image_path))
            predicted_plate = result.get("text", "")
            exact_match = normalize(predicted_plate) == normalize(expected_plate)
            rows.append({
                "file": file_name,
                "expected_plate": expected_plate,
                "predicted_plate": predicted_plate,
                "confidence": result.get("confidence", 0.0),
                "is_usable": result.get("is_usable", False),
                "exact_match": exact_match,
                "quality_note": result.get("quality_note", ""),
                "notes": notes,
            })

    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "expected_plate", "predicted_plate", "confidence", "is_usable", "exact_match", "quality_note", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    exact = sum(1 for row in rows if str(row["exact_match"]).lower() == "true")
    usable = sum(1 for row in rows if str(row["is_usable"]).lower() == "true")
    print("benchmark_target=run_alpr (ground-truth baseline benchmark)")
    print(f"uploads_dir={UPLOADS_DIR}")
    print(f"done,{len(rows)},{exact},{usable},{out_csv}")


if __name__ == "__main__":
    main()
