from backend import alpr_service


class DummyOCR(alpr_service.EasyOCRVNOCR):
    def __init__(self):
        pass


def test_deep_retry_selects_better_full_result(monkeypatch):
    monkeypatch.setattr(alpr_service, "FAST_MODE", True)
    monkeypatch.setattr(alpr_service, "ENABLE_DEEP_OCR_RETRY", True)
    ocr = DummyOCR()
    calls = []

    def fake_core(cropped_plate, force_full=False):
        calls.append(force_full)
        if force_full:
            return alpr_service.OcrResult(text="65-D1 123.45", confidence=0.95)
        return alpr_service.OcrResult(text="65-D1", confidence=0.52)

    monkeypatch.setattr(ocr, "_predict_core", fake_core)

    result = ocr.predict(type("Image", (), {"shape": (100, 100, 3)})())

    assert calls == [False, True]
    assert result.text == "65-D1 123.45"


def test_deep_retry_skips_when_fast_result_good(monkeypatch):
    monkeypatch.setattr(alpr_service, "FAST_MODE", True)
    monkeypatch.setattr(alpr_service, "ENABLE_DEEP_OCR_RETRY", True)
    ocr = DummyOCR()
    calls = []

    def fake_core(cropped_plate, force_full=False):
        calls.append(force_full)
        return alpr_service.OcrResult(text="65-D1 123.45", confidence=0.95)

    monkeypatch.setattr(ocr, "_predict_core", fake_core)

    result = ocr.predict(type("Image", (), {"shape": (100, 100, 3)})())

    assert calls == [False]
    assert result.text == "65-D1 123.45"
