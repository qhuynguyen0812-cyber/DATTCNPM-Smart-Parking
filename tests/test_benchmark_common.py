import pytest

pytestmark = pytest.mark.benchmark


from scripts import benchmark_common


def test_evaluate_image_uses_process_plate_image(monkeypatch, tmp_path):
    called = {}

    class StubProcessed:
        def __init__(self):
            self.ocr = {"text": "66-B1 069.99", "is_usable": True, "confidence": 0.88}

    def fake_process_plate_image(path):
        called["path"] = path
        return StubProcessed()

    monkeypatch.setattr(benchmark_common, "process_plate_image", fake_process_plate_image)
    image_path = tmp_path / "sample.jpg"
    image_path.write_bytes(b"fake")

    result = benchmark_common.evaluate_image(image_path)

    assert called["path"] == str(image_path)
    assert result["text"] == "66-B1 069.99"
