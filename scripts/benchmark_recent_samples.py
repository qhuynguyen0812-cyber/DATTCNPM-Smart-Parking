import csv
from pathlib import Path

from scripts.benchmark_common import ROOT, evaluate_image, resolve_benchmark_uploads_dir


def pick_images(base: Path, limit_per_prefix: int = 8):
    prefixes = ["entry_", "exit_", "z"]
    chosen = []
    for prefix in prefixes:
        files = sorted(base.glob(f"{prefix}*.jpg")) + sorted(base.glob(f"{prefix}*.png")) + sorted(base.glob(f"{prefix}*.jpeg"))
        chosen.extend(files[:limit_per_prefix])
    return chosen


def main():
    base = resolve_benchmark_uploads_dir()
    out_csv = ROOT / "data" / "benchmark" / "results" / "benchmark_recent_samples.csv"
    images = pick_images(base)
    rows = []
    for idx, image_path in enumerate(images, start=1):
        try:
            result = evaluate_image(image_path)
            rows.append({
                "index": idx,
                "file": image_path.name,
                "text": result.get("text", ""),
                "raw_text": result.get("raw_text", ""),
                "confidence": result.get("confidence", 0.0),
                "is_usable": result.get("is_usable", False),
                "quality_note": result.get("quality_note", ""),
                "message": result.get("message", ""),
            })
        except Exception as exc:
            rows.append({
                "index": idx,
                "file": image_path.name,
                "text": "",
                "raw_text": "",
                "confidence": 0.0,
                "is_usable": False,
                "quality_note": f"exception: {exc}",
                "message": "exception",
            })

    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "file", "text", "raw_text", "confidence", "is_usable", "quality_note", "message"])
        writer.writeheader()
        writer.writerows(rows)

    usable = sum(1 for row in rows if str(row["is_usable"]).lower() == "true")
    print(f"done,{len(rows)},{usable},{out_csv}")


if __name__ == "__main__":
    main()
