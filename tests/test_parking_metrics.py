import pandas as pd

from backend.parking_metrics import build_parking_kpis, classify_operational_health


def test_build_parking_kpis_counts_business_states():
    df = pd.DataFrame([
        {"status": "IN_PARKING", "match_result": "PENDING", "entry_ocr_confidence": 0.9, "entry_manual_override": 0, "exit_manual_override": 0},
        {"status": "COMPLETED", "match_result": "MATCH", "entry_ocr_confidence": 0.8, "entry_manual_override": 1, "exit_manual_override": 0},
        {"status": "NEEDS_REVIEW", "match_result": "MISMATCH", "entry_ocr_confidence": 0.4, "entry_manual_override": 0, "exit_manual_override": 1},
        {"status": "CANCELLED", "match_result": "PENDING", "entry_ocr_confidence": None, "entry_manual_override": 0, "exit_manual_override": 0},
    ])

    kpis = build_parking_kpis(df)

    assert kpis.total_tickets == 4
    assert kpis.active_tickets == 1
    assert kpis.completed_tickets == 1
    assert kpis.review_tickets == 1
    assert kpis.cancelled_tickets == 1
    assert kpis.mismatch_tickets == 1
    assert kpis.manual_override_tickets == 2
    assert round(kpis.avg_confidence, 2) == 0.70
    assert kpis.review_rate == 0.25
    assert kpis.mismatch_rate == 0.25


def test_classify_operational_health_flags_review_queue():
    kpis = build_parking_kpis(pd.DataFrame([{"status": "NEEDS_REVIEW", "match_result": "MISMATCH"}]))

    assert classify_operational_health(kpis) == ("ATTENTION_REQUIRED", "warning")
