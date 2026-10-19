import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr
from backend.config import BENCHMARK_UPLOADS_DIR, REPORT_DIR

DATASET_CSV = ROOT / "data" / "benchmark" / "datasets" / "benchmark_dataset.csv"
OUT_CSV = ROOT / "data" / "benchmark" / "ground_truth" / "benchmark_dataset_ground_truth_template.csv"
PREVIEW_MD = REPORT_DIR / "benchmark_ground_truth_preview.md"


def main():
    if not DATASET_CSV.exists():
        raise SystemExit(f"Missing dataset file: {DATASET_CSV}")

    rows = []
    preview_lines = ["# Benchmark Ground Truth Preview", "", "Dùng file CSV để điền `expected_plate` chuẩn cho từng ảnh.", ""]

    with DATASET_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, item in enumerate(reader, start=1):
            file_name = (item.get("file") or "").strip()
            expected_plate = (item.get("expected_plate") or "").strip()
            label = (item.get("label") or "todo").strip().lower()
            notes = (item.get("notes") or "").strip()
            image_path = BENCHMARK_UPLOADS_DIR / file_name

            ocr_text = ""
            quality_note = "missing file"
            if image_path.exists():
                result = run_alpr(str(image_path))
                ocr_text = result.get("text", "")
                quality_note = result.get("quality_note", "")

            rows.append(
                {
                    "file": file_name,
                    "expected_plate": expected_plate,
                    "ocr_suggestion": ocr_text,
                    "label": label,
                    "notes": notes,
                }
            )

            preview_lines.extend(
                [
                    f"## {idx}. {file_name}",
                    f"- OCR suggestion: `{ocr_text or '(empty)'}`",
                    f"- Label: `{label}`",
                    f"- Notes: {notes or quality_note or '-'}",
                    "",
                ]
            )

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "expected_plate", "ocr_suggestion", "label", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    PREVIEW_MD.write_text("\n".join(preview_lines), encoding="utf-8")

    print(OUT_CSV)
    print(PREVIEW_MD)
    print(f"count={len(rows)}")


if __name__ == "__main__":
    main()
