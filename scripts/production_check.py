from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.production_readiness import check_production_readiness, summarize_findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-ok", action="store_true", help="Treat demo-only limitations as warnings instead of hard failures")
    args = parser.parse_args()
    findings = check_production_readiness(demo_ok=args.demo_ok)
    summary = summarize_findings(findings)
    print("Production readiness check")
    print("=" * 40)
    for item in findings:
        print(f"[{item.status.upper()}] {item.name}: {item.detail}")
    print(f"Summary: pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}")
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
