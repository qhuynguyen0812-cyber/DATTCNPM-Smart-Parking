import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.plate_format import format_vn_plate

INPUT_CSV = ROOT / "data" / "benchmark" / "ground_truth" / "benchmark_dataset_ground_truth_template.csv"
OUTPUT_CSV = ROOT / "data" / "benchmark" / "ground_truth" / "benchmark_dataset_prefilled.csv"
REVIEW_MD = ROOT / "data" / "benchmark" / "review" / "benchmark_ground_truth_review_queue.md"

SAFE_PATTERNS = (
    re.compile(r"^\d{2}-[A-Z]\d \d{3}\.\d{2}$"),
    re.compile(r"^\d{2}-[A-Z]{2} \d{4}$"),
    re.compile(r"^\d{2}-[A-Z]{2} \d{3}\.\d{2}$"),
    re.compile(r"^\d{2}-[A-Z]\d \d{4}$"),
)


def classify_prefill(suggestion: str):
    formatted = format_vn_plate(suggestion or "")
    if not formatted:
        return "", "bad", "manual review required: empty OCR suggestion"
    if any(pattern.fullmatch(formatted) for pattern in SAFE_PATTERNS):
        return formatted, "medium", "prefilled from strong OCR suggestion"
    if len(formatted) >= 7:
        return "", "bad", f"manual review required: ambiguous suggestion `{formatted}`"
    return "", "bad", "manual review required: weak OCR suggestion"


def main():
    if not INPUT_CSV.exists():
        raise SystemExit(f"Missing input csv: {INPUT_CSV}")

    rows = []
    review_lines = ["# Ground Truth Review Queue", "", "Các dòng dưới đây cần rà tay trước khi dùng cho benchmark exact-match.", ""]

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, item in enumerate(reader, start=1):
            file_name = (item.get("file") or "").strip()
            expected_plate = (item.get("expected_plate") or "").strip()
            ocr_suggestion = (item.get("ocr_suggestion") or "").strip()
            label = (item.get("label") or "todo").strip().lower()
            notes = (item.get("notes") or "").strip()

            prefilled_plate = expected_plate
            prefilled_label = label
            prefilled_note = notes

            if not expected_plate:
                candidate_plate, candidate_label, candidate_note = classify_prefill(ocr_suggestion)
                prefilled_plate = candidate_plate
                prefilled_label = candidate_label
                prefilled_note = candidate_note

            if not prefilled_plate:
                review_lines.extend(
                    [
                        f"## {idx}. {file_name}",
                        f"- OCR suggestion: `{ocr_suggestion or '(empty)'}`",
                        f"- Current note: {prefilled_note}",
                        "",
                    ]
                )

            rows.append(
                {
                    "file": file_name,
                    "expected_plate": prefilled_plate,
                    "ocr_suggestion": ocr_suggestion,
                    "label": prefilled_label,
                    "notes": prefilled_note,
                }
            )

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "expected_plate", "ocr_suggestion", "label", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    REVIEW_MD.write_text("\n".join(review_lines), encoding="utf-8")
    print(OUTPUT_CSV)
    print(REVIEW_MD)
    print(f"count={len(rows)}")


if __name__ == "__main__":
    main()
