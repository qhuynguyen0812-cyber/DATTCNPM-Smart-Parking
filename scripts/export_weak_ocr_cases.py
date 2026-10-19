from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import REPORT_DIR


def export_weak_cases(report_json: Path, output_dir: Path | None = None) -> dict:
    data = json.loads(report_json.read_text(encoding="utf-8"))
    output_dir = output_dir or (REPORT_DIR / "weak_ocr_cases")
    output_dir.mkdir(parents=True, exist_ok=True)
    weak = []
    for sample in data.get("samples", []):
        note = sample.get("quality_note", "")
        is_weak = (not sample.get("text")) or sample.get("confidence", 0.0) < 0.75 or "ngắn" in note or "phần" in note
        if not is_weak:
            continue
        source = Path(sample["image"])
        target = output_dir / source.name
        if source.exists():
            shutil.copy2(source, target)
        weak.append({**sample, "exported_path": str(target)})
    summary = {"count": len(weak), "output_dir": str(output_dir), "items": weak}
    (output_dir / "weak_cases.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=str(REPORT_DIR / "bike_back_real_ocr.json"))
    args = parser.parse_args()
    summary = export_weak_cases(Path(args.report))
    print(f"Exported weak OCR cases: {summary['count']}")
    print(f"Output: {summary['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
