from pathlib import Path

import pandas as pd

from scripts.operational_report import build_daily_report, write_report_csv


def test_build_daily_report_counts_metrics():
    df = pd.DataFrame([
        {"ticket_id": "T1", "entry_time": "2026-04-25 08:00:00", "exit_time": "2026-04-25 10:00:00",
         "match_result": "MATCH", "entry_manual_override": 0, "exit_manual_override": 0, "review_required": 0},
        {"ticket_id": "T2", "entry_time": "2026-04-25 11:00:00", "exit_time": None,
         "match_result": None, "entry_manual_override": 1, "exit_manual_override": 0, "review_required": 0},
        {"ticket_id": "T3", "entry_time": "2026-04-26 09:00:00", "exit_time": "2026-04-26 11:00:00",
         "match_result": "MISMATCH", "entry_manual_override": 0, "exit_manual_override": 1, "review_required": 1},
    ])

    rows = build_daily_report(df)

    by_date = {row["date"]: row for row in rows}
    assert by_date["2026-04-25"]["entries"] == 2
    assert by_date["2026-04-25"]["exits"] == 1
    assert by_date["2026-04-25"]["manual_overrides"] == 1
    assert by_date["2026-04-26"]["entries"] == 1
    assert by_date["2026-04-26"]["mismatches"] == 1
    assert by_date["2026-04-26"]["reviews"] == 1


def test_build_daily_report_empty():
    assert build_daily_report(pd.DataFrame()) == []


def test_write_report_csv(tmp_path):
    rows = [{"date": "2026-04-25", "entries": 2, "exits": 1}]
    out = write_report_csv(rows, tmp_path / "report.csv")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "date,entries,exits" in text
    assert "2026-04-25,2,1" in text
