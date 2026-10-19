from backend import alpr_service


def test_accuracy_mode_compares_fast_and_paddle(monkeypatch):
    monkeypatch.setattr(alpr_service, "OCR_ACCURACY_MODE", True)
    monkeypatch.setattr(alpr_service, "ENABLE_PADDLE_FALLBACK", True)
    monkeypatch.setattr(alpr_service, "ENABLE_PADDLE_OCR", False)
    monkeypatch.setattr(alpr_service, "_is_good_enough", lambda payload: True)
    monkeypatch.setattr(alpr_service, "load_fast_alpr", lambda detector_model=None: None)
    monkeypatch.setattr(alpr_service, "_load_runtime_frame", lambda image_path: object())
    monkeypatch.setattr(alpr_service, "_run_paddle_ocr", lambda image_path, detector_label, annotated_path: {
        "text": "65-D1 123.45",
        "confidence": 0.95,
        "ocr_engine": "paddleocr",
        "is_usable": True,
    })

    result = alpr_service.run_alpr("sample.jpg")

    assert result["ocr_engine"] == "paddleocr"
    assert result["text"] == "65-D1 123.45"


def test_speed_mode_returns_good_fast_payload_without_paddle(monkeypatch):
    monkeypatch.setattr(alpr_service, "OCR_ACCURACY_MODE", False)
    monkeypatch.setattr(alpr_service, "ENABLE_PADDLE_FALLBACK", True)
    monkeypatch.setattr(alpr_service, "_is_good_enough", lambda payload: True)
    monkeypatch.setattr(alpr_service, "_load_runtime_frame", lambda image_path: object())

    class FakeOcr:
        text = "65-D1 123.45"
        confidence = 0.95

    class FakeDetection:
        confidence = 0.9

    class FakeResult:
        ocr = FakeOcr()
        detection = FakeDetection()

    class FakeDrawn:
        results = [FakeResult()]
        image = object()

    class FakeAlpr:
        def draw_predictions(self, frame):
            return FakeDrawn()

    called = {"paddle": False}
    monkeypatch.setattr(alpr_service, "load_fast_alpr", lambda detector_model=None: FakeAlpr())
    monkeypatch.setattr(alpr_service, "save_annotated_image", lambda cv2, image, prefix: "annotated.jpg")
    monkeypatch.setattr(alpr_service, "_run_paddle_ocr", lambda *args: called.__setitem__("paddle", True))

    result = alpr_service.run_alpr("sample.jpg")

    assert result["ocr_engine"] == "fast-alpr-easyocr"
    assert called["paddle"] is False
