import csv
from pathlib import Path

UPLOADS_DIR = Path(r"C:\Users\huy81\plate_demo_data\uploads")
OUT_CSV = Path(r"C:\Users\huy81\.openclaw\workspace\tmp\-ITS-\benchmark_candidates.csv")


def pick_candidates(limit_per_prefix: int = 15):
    prefixes = ["entry_", "exit_", "alpr_", "z"]
    chosen = []
    for prefix in prefixes:
        files = sorted(UPLOADS_DIR.glob(f"{prefix}*.jpg"))
        chosen.extend(files[:limit_per_prefix])
    return chosen


def main():
    rows = []
    for image_path in pick_candidates():
        rows.append(
            {
                "file": image_path.name,
                "expected_plate": "",
                "label": "candidate",
                "notes": "fill manually after review",
            }
        )

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "expected_plate", "label", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    print(OUT_CSV)
    print(f"count={len(rows)}")


if __name__ == "__main__":
    main()
