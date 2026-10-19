import csv

from scripts.benchmark_common import DATASET_CSV, ROOT, evaluate_image, iter_dataset_rows, normalize, resolve_benchmark_uploads_dir

OUT_CSV = ROOT / "data" / "benchmark" / "results" / "benchmark_badcase_results.csv"
UPLOADS_DIR = resolve_benchmark_uploads_dir()

def main():
    rows = []
    for item in iter_dataset_rows(DATASET_CSV):
        if (item.get("label") or "").strip().lower() != "bad":
            continue
        file_name = (item.get("file") or "").strip()
        expected_plate = (item.get("expected_plate") or "").strip()
        image_path = UPLOADS_DIR / file_name
        if not image_path.exists():
            continue
        ocr = evaluate_image(image_path)
        predicted_plate = ocr.get("text", "")
        rows.append(
            {
                "file": file_name,
                "expected_plate": expected_plate,
                "predicted_plate": predicted_plate,
                "is_usable": ocr.get("is_usable", False),
                "exact_match": normalize(predicted_plate) == normalize(expected_plate) if expected_plate else False,
                "confidence": ocr.get("confidence", 0.0),
                "variant": ocr.get("variant", "baseline"),
                "quality_note": ocr.get("quality_note", ""),
            }
        )

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "expected_plate", "predicted_plate", "is_usable", "exact_match", "confidence", "variant", "quality_note"])
        writer.writeheader()
        writer.writerows(rows)

    print(OUT_CSV)
    print("benchmark_target=process_plate_image")
    print(f"uploads_dir={UPLOADS_DIR}")
    print(f"count={len(rows)}")


if __name__ == "__main__":
    main()
