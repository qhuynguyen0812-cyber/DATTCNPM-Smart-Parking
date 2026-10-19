import pytest

pytestmark = pytest.mark.benchmark


from scripts import benchmark_bad_cases


def test_bad_case_benchmark_uses_configured_upload_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(benchmark_bad_cases, "UPLOADS_DIR", tmp_path)
    assert benchmark_bad_cases.UPLOADS_DIR == tmp_path
