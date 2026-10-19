from backend.benchmarking import compute_benchmark_metrics


def test_compute_benchmark_metrics_scores_accuracy_and_latency():
    rows = [
        {"expected_plate": "66-B1 123.45", "predicted_plate": "66-B1 123.45", "latency_ms": 40, "confidence": 0.9},
        {"expected_plate": "66-B1 123.45", "predicted_plate": "66B112345", "latency_ms": 60, "confidence": 0.8},
        {"expected_plate": "59-C2 999.99", "predicted_plate": "", "latency_ms": 100, "confidence": 0.1},
    ]

    metrics = compute_benchmark_metrics(rows)

    assert metrics.total_samples == 3
    assert metrics.exact_matches == 1
    assert metrics.normalized_matches == 2
    assert metrics.unreadable == 1
    assert round(metrics.exact_accuracy, 2) == 0.33
    assert round(metrics.normalized_accuracy, 2) == 0.67
    assert metrics.average_latency_ms == 200 / 3
