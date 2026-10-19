from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import REPORT_DIR
from backend.cv_readiness import build_cv_readiness


def write_cv_reports(report_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    payload = build_cv_readiness()
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "cv_readiness_report.json"
    md_path = report_dir / "cv_readiness_report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# CV/OCR Readiness Report", "", f"Pipeline grade: **{payload['pipeline_grade']}**", "", "## Checks", ""]
    for item in payload["checks"]:
        lines.append(f"- **{item['name']}**: `{item['status']}` — {item['detail']}")
    lines.extend(["", "## External detector models", ""])
    if payload["models"]:
        for model in payload["models"]:
            lines.append(f"- `{model['name']}` — {model['size_mb']} MB")
    else:
        lines.append("- No external `.pt` models found.")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    payload = build_cv_readiness()
    json_path, md_path = write_cv_reports()
    print("CV/OCR doctor")
    print("=" * 40)
    for item in payload["checks"]:
        print(f"[{item['status'].upper()}] {item['name']}: {item['detail']}")
    print(f"Models: {len(payload['models'])}")
    print(f"Reports: {json_path} | {md_path}")
    return 1 if payload["summary"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
