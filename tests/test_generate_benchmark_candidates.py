import pytest

pytestmark = pytest.mark.benchmark


from scripts import generate_benchmark_candidates


def test_generate_candidates_uses_repo_relative_output(monkeypatch, tmp_path):
    root = generate_benchmark_candidates.ROOT
    expected_csv = root / "data" / "benchmark" / "review" / "benchmark_candidates.csv"
    monkeypatch.setattr(generate_benchmark_candidates, "UPLOADS_DIR", tmp_path)
    monkeypatch.setattr(generate_benchmark_candidates, "OUT_CSV", expected_csv)
    assert generate_benchmark_candidates.UPLOADS_DIR == tmp_path
    assert generate_benchmark_candidates.OUT_CSV == expected_csv
