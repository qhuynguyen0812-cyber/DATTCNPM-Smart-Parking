from __future__ import annotations

import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app
from backend.config import REPORT_DIR


def compute_latency_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "average_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))
    return {"count": len(values), "average_ms": statistics.mean(values), "p95_ms": ordered[index], "max_ms": max(values)}


def run_smoke(iterations: int = 30) -> dict:
    client = TestClient(app)
    endpoints = ["/health", "/readiness", "/system/scorecard"]
    results = {}
    for endpoint in endpoints:
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            response = client.get(endpoint)
            elapsed = (time.perf_counter() - start) * 1000
            if response.status_code >= 500:
                raise RuntimeError(f"{endpoint} returned {response.status_code}")
            latencies.append(elapsed)
        results[endpoint] = compute_latency_stats(latencies)
    return results


def write_performance_reports(results: dict, report_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "performance_smoke.json"
    md_path = report_dir / "performance_smoke.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# API Performance Smoke Report", ""]
    for endpoint, stats in results.items():
        lines.append(f"## `{endpoint}`")
        lines.append(f"- Count: **{stats['count']}**")
        lines.append(f"- Average: **{stats['average_ms']:.2f} ms**")
        lines.append(f"- P95: **{stats['p95_ms']:.2f} ms**")
        lines.append(f"- Max: **{stats['max_ms']:.2f} ms**")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    results = run_smoke()
    json_path, md_path = write_performance_reports(results)
    print("Performance smoke")
    print("=" * 40)
    for endpoint, stats in results.items():
        print(f"{endpoint}: avg={stats['average_ms']:.2f}ms p95={stats['p95_ms']:.2f}ms")
    print(f"Reports: {json_path} | {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
