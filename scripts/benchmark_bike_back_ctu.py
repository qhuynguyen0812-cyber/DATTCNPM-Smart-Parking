import csv
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app_service import process_plate_image

DATASET_DIR = Path(r"C:\Users\nhock\Downloads\Bike_back_ctu\Bike_back_ctu\Bike_back")
OUT_CSV = ROOT / "data" / "benchmark" / "results" / "benchmark_bike_back_ctu_results.csv"
SUMMARY_TXT = ROOT / "data" / "benchmark" / "results" / "benchmark_bike_back_ctu_summary.txt"


def main():
    images = sorted([p for p in DATASET_DIR.glob("*.jpg") if p.is_file()])
    if not images:
        raise SystemExit(f"No JPG files found in {DATASET_DIR}")

    rows = []
    durations = []
    success_text = 0
    usable = 0
    errors = 0

    for idx, image_path in enumerate(images, start=1):
        started = time.perf_counter()
        try:
            processed = process_plate_image(str(image_path), ocr_engine="fast-alpr-easyocr", use_hardcase=False)
            ocr = processed.ocr
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            durations.append(duration_ms)
            text = (ocr.get("text") or "").strip()
            is_usable = bool(ocr.get("is_usable", False))
            if text:
                success_text += 1
            if is_usable:
                usable += 1
            rows.append({
                "index": idx,
                "file": image_path.name,
                "predicted_plate": text,
                "raw_text": (ocr.get("raw_text") or "").strip(),
                "plate_type": ocr.get("plate_type", ""),
                "confidence": ocr.get("confidence", 0.0),
                "is_usable": is_usable,
                "quality_note": ocr.get("quality_note", ""),
                "ocr_engine": ocr.get("ocr_engine", ""),
                "duration_ms": duration_ms,
            })
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            durations.append(duration_ms)
            errors += 1
            rows.append({
                "index": idx,
                "file": image_path.name,
                "predicted_plate": "",
                "raw_text": "",
                "plate_type": "",
                "confidence": 0.0,
                "is_usable": False,
                "quality_note": f"exception: {type(exc).__name__}: {exc}",
                "ocr_engine": "exception",
                "duration_ms": duration_ms,
            })

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index", "file", "predicted_plate", "raw_text", "plate_type", "confidence",
                "is_usable", "quality_note", "ocr_engine", "duration_ms"
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "dataset_dir": str(DATASET_DIR),
        "count": len(images),
        "predicted_non_empty": success_text,
        "usable": usable,
        "errors": errors,
        "avg_ms": round(statistics.mean(durations), 2),
        "median_ms": round(statistics.median(durations), 2),
        "p95_ms": round(sorted(durations)[max(0, min(len(durations) - 1, int(len(durations) * 0.95) - 1))], 2),
        "results_csv": str(OUT_CSV),
    }
    SUMMARY_TXT.write_text("\n".join(f"{k}={v}" for k, v in summary.items()), encoding="utf-8")
    print(SUMMARY_TXT)
    for k, v in summary.items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
