from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.benchmarking import run_static_benchmark
from backend.config import BENCHMARK_UPLOADS_DIR, REPORT_DIR


def _default_csv() -> Path:
    candidate = ROOT / "data" / "benchmark" / "datasets" / "benchmark_dataset.csv"
    return candidate if candidate.exists() else BENCHMARK_UPLOADS_DIR / "benchmark_dataset.csv"


def write_reports(metrics, report_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "benchmark_report.json"
    md_path = report_dir / "benchmark_report.md"
    payload = metrics.as_dict()
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(
        "# OCR/CV Benchmark Report\n\n"
        f"- Total samples: **{metrics.total_samples}**\n"
        f"- Exact accuracy: **{metrics.exact_accuracy:.2%}**\n"
        f"- Normalized plate accuracy: **{metrics.normalized_accuracy:.2%}**\n"
        f"- Unreadable rate: **{metrics.unreadable_rate:.2%}**\n"
        f"- Average latency: **{metrics.average_latency_ms:.2f} ms**\n"
        f"- P95 latency: **{metrics.p95_latency_ms:.2f} ms**\n"
        f"- Average confidence: **{metrics.average_confidence:.2f}**\n",
        encoding="utf-8",
    )
    return json_path, md_path


def main() -> int:
    csv_path = _default_csv()
    metrics = run_static_benchmark(csv_path)
    json_path, md_path = write_reports(metrics)
    print("OCR/CV benchmark")
    print("=" * 40)
    print(f"Dataset: {csv_path}")
    print(f"Total samples: {metrics.total_samples}")
    print(f"Exact accuracy: {metrics.exact_accuracy:.2%}")
    print(f"Normalized accuracy: {metrics.normalized_accuracy:.2%}")
    print(f"Unreadable rate: {metrics.unreadable_rate:.2%}")
    print(f"Average latency: {metrics.average_latency_ms:.2f} ms")
    print(f"Reports: {json_path} | {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
