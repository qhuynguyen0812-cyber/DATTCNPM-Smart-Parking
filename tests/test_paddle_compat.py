import pytest

pytestmark = pytest.mark.ocr


from backend import alpr_service


class LegacyStylePaddle:
    def __init__(self, **kwargs):
        if "show_log" in kwargs:
            raise ValueError("Unknown argument: show_log")

    def ocr(self, image_path, cls=True):
        return [[[[0, 0], [1, 0], [1, 1], [0, 1]], ("66B106999", 0.91)]]


class NewStylePaddle:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def predict(self, input):
        return [{"rec_texts": ["66B106999"], "rec_scores": [0.93]}]


def test_get_paddle_reader_falls_back_when_show_log_is_unsupported(monkeypatch):
    monkeypatch.setattr(alpr_service, "ENABLE_PADDLE_OCR", True)
    monkeypatch.setattr(alpr_service, "PaddleOCR", LegacyStylePaddle)
    monkeypatch.setattr(alpr_service, "_PADDLE_OCR_READER", None)

    reader = alpr_service._get_paddle_reader()

    assert reader is not None


def test_run_paddle_ocr_supports_new_predict_shape(monkeypatch):
    monkeypatch.setattr(alpr_service, "ENABLE_PADDLE_OCR", True)
    monkeypatch.setattr(alpr_service, "PaddleOCR", NewStylePaddle)
    monkeypatch.setattr(alpr_service, "_PADDLE_OCR_READER", None)

    payload = alpr_service._run_paddle_ocr("sample.jpg", "detector", "annotated.jpg")

    assert payload is not None
    assert payload["ocr_engine"] == "paddleocr"
    assert payload["text"] == "66-B1 069.99"
    assert payload["confidence"] == 0.93
