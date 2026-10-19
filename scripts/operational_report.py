from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import pandas as pd

from backend.config import REPORT_DIR
from backend.db import fetch_logs


def build_daily_report(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    logs = df.copy()
    if "entry_time" not in logs.columns:
        return []

    logs["_date"] = logs["entry_time"].astype(str).str[:10]
    rows = []
    for date, group in logs.groupby("_date", sort=False):
        row = {"date": date, "entries": int(len(group))}
        if "exit_time" in logs.columns:
            row["exits"] = int(group["exit_time"].notna().sum())
        if "match_result" in logs.columns:
            row["mismatches"] = int((group["match_result"] == "MISMATCH").sum())
        manual_cols = [col for col in ("entry_manual_override", "exit_manual_override") if col in logs.columns]
        if manual_cols:
            row["manual_overrides"] = int((group[manual_cols].fillna(0).astype(int).sum(axis=1) > 0).sum())
        if "review_required" in logs.columns:
            row["reviews"] = int((group["review_required"].fillna(0).astype(int) > 0).sum())
        rows.append(row)
    return rows


def write_report_csv(rows: list[dict], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("date,entries\n", encoding="utf-8")
        return output_path
    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a daily operational report from parking logs.")
    parser.add_argument("--out", help="Output CSV path (default: reports/daily-report-<timestamp>.csv)")
    args = parser.parse_args()

    rows = build_daily_report(fetch_logs())
    if not rows:
        print("No parking logs to report.")
        return 0

    output = Path(args.out) if args.out else (REPORT_DIR / f"daily-report-{datetime.now().strftime('%Y%m%d')}.csv")
    write_report_csv(rows, output)
    print(f"Report written to {output} ({len(rows)} day(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
