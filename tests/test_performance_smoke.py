from scripts.performance_smoke import compute_latency_stats


def test_compute_latency_stats_reports_average_and_p95():
    stats = compute_latency_stats([10, 20, 30, 40, 50])

    assert stats["count"] == 5
    assert stats["average_ms"] == 30
    assert stats["p95_ms"] >= 40
    assert stats["max_ms"] == 50
