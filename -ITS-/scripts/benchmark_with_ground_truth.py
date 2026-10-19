import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr
from backend.plate_format import normalize_plate_text


UPLOADS_DIR = Path(r"C:\Users\huy81\plate_demo_data\uploads")


def main():
    truth_csv = ROOT / "benchmark_ground_truth_template.csv"
    out_csv = ROOT / "benchmark_ground_truth_results.csv"
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
            exact_match = normalize_plate_text(predicted_plate) == normalize_plate_text(expected_plate)
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
    print(f"done,{len(rows)},{exact},{usable},{out_csv}")


if __name__ == "__main__":
    main()
