from scripts.benchmark_inference import run_inference_benchmark, write_inference_reports


def test_inference_benchmark_handles_missing_images(tmp_path):
    csv_path = tmp_path / "field.csv"
    csv_path.write_text("image_path,expected_plate\nmissing.jpg,66-B1 123.45\n", encoding="utf-8")

    payload = run_inference_benchmark(csv_path)
    json_path, md_path = write_inference_reports(payload, tmp_path)

    assert payload["field_images_available"] is False
    assert payload["runnable_images"] == 0
    assert json_path.exists()
    assert md_path.exists()
