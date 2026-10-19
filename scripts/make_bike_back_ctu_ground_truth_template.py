import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = Path(r"C:\Users\nhock\Downloads\Bike_back_ctu\Bike_back_ctu\Bike_back")
OUT_CSV = ROOT / "data" / "benchmark" / "ground_truth" / "bike_back_ctu_ground_truth_template.csv"


def main():
    images = sorted([p for p in DATASET_DIR.glob("*.jpg") if p.is_file()])
    if not images:
        raise SystemExit(f"No JPG files found in {DATASET_DIR}")

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "expected_plate", "label", "notes"])
        writer.writeheader()
        for image_path in images:
            writer.writerow({
                "file": image_path.name,
                "expected_plate": "",
                "label": "todo",
                "notes": "fill manually",
            })

    print(OUT_CSV)
    print(f"count={len(images)}")


if __name__ == "__main__":
    main()
