import csv

from scripts.benchmark_common import ROOT, resolve_benchmark_uploads_dir

UPLOADS_DIR = resolve_benchmark_uploads_dir()
OUT_CSV = ROOT / "data" / "benchmark" / "review" / "benchmark_candidates.csv"


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

    print(f"uploads_dir={UPLOADS_DIR}")
    print(OUT_CSV)
    print(f"count={len(rows)}")


if __name__ == "__main__":
    main()
