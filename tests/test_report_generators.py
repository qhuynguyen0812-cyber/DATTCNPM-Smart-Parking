from scripts.generate_evaluation_report import generate_report
from scripts.run_benchmark import write_reports
from backend.benchmarking import compute_benchmark_metrics


def test_report_generators_create_files(tmp_path):
    metrics = compute_benchmark_metrics([
        {"expected_plate": "66-B1 123.45", "predicted_plate": "66-B1 123.45", "latency_ms": 50, "confidence": 0.9}
    ])
    json_path, md_path = write_reports(metrics, tmp_path)
    eval_path = generate_report(tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    assert eval_path.exists()
    assert "Strict Scoring Projection" in eval_path.read_text(encoding="utf-8")
