import pytest

from scripts import benchmark_with_ground_truth

pytestmark = pytest.mark.benchmark


def test_ground_truth_benchmark_uses_configured_upload_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(benchmark_with_ground_truth, "UPLOADS_DIR", tmp_path)
    assert benchmark_with_ground_truth.UPLOADS_DIR == tmp_path


def test_ground_truth_benchmark_writes_missing_file_row(monkeypatch, tmp_path):
    truth_csv = tmp_path / "truth.csv"
    truth_csv.write_text(
        "file,expected_plate,notes\nmissing.jpg,66-B1 069.99,bad sample\n",
        encoding="utf-8",
    )
    out_csv = tmp_path / "out.csv"

    monkeypatch.setattr(benchmark_with_ground_truth, "TRUTH_CSV", truth_csv)
    monkeypatch.setattr(benchmark_with_ground_truth, "OUT_CSV", out_csv)
    monkeypatch.setattr(benchmark_with_ground_truth, "UPLOADS_DIR", tmp_path / "uploads")

    benchmark_with_ground_truth.main()

    content = out_csv.read_text(encoding="utf-8-sig")
    assert "missing.jpg" in content
    assert "missing file" in content
    assert "66-B1 069.99" in content
