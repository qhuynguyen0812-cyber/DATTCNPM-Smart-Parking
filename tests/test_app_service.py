from backend import app_service


class StubProcessed:
    def __init__(self):
        self.ocr = {
            "text": "66-B1 069.99",
            "confidence": 0.88,
            "annotated_path": "annotated.jpg",
            "is_usable": True,
            "quality_note": "Biển số hợp lệ",
            "candidates": [
                {"text": "66-B1 069.99", "confidence": 0.88, "is_usable": True},
                {"text": "66-B1 069.98", "confidence": 0.75, "is_usable": False},
            ],
        }
        self.plate_text = "66-B1 069.99"


def test_process_plate_image_returns_processed_plate():
    processed = app_service.process_plate_image(
        "sample.jpg",
        detector_model="model.pt",
        alpr_runner=lambda image_path, detector_model=None: StubProcessed().ocr,
    )

    assert processed.plate_text == "66-B1 069.99"
    assert processed.ocr["annotated_path"] == "annotated.jpg"
    assert len(processed.ocr["candidates"]) == 2


def test_confirm_vehicle_entry_validates_before_saving(monkeypatch):
    called = {}

    def fake_validate_plate_text(value):
        called["validated"] = value
        return "66-B1 069.99"

    def fake_vehicle_entry(*args, **kwargs):
        called["saved"] = {"args": args, "kwargs": kwargs}
        return {"success": True, "ticket_id": "T1"}

    monkeypatch.setattr(app_service, "validate_plate_text", fake_validate_plate_text)
    monkeypatch.setattr(app_service, "vehicle_entry", fake_vehicle_entry)

    result = app_service.confirm_vehicle_entry("66b106999", image_path="img.jpg", ocr_text="66B106999", manual_override=True)

    assert result["success"] is True
    assert called["validated"] == "66b106999"
    assert called["saved"]["args"][0] == "66-B1 069.99"
    assert called["saved"]["kwargs"]["ocr_text"] == "66B106999"
    assert called["saved"]["kwargs"]["manual_override"] is True


def test_confirm_vehicle_entry_rejects_invalid_manual_plate(monkeypatch):
    def fake_validate_plate_text(value):
        raise ValueError("Invalid plate text: Mới đọc được một phần biển số")

    monkeypatch.setattr(app_service, "validate_plate_text", fake_validate_plate_text)

    try:
        app_service.confirm_vehicle_entry("66B1", image_path="img.jpg")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid plate text" in str(exc)


def test_confirm_vehicle_exit_validates_ticket_and_plate(monkeypatch):
    called = {}

    monkeypatch.setattr(app_service, "validate_ticket_id", lambda value: "TICKET-1")
    monkeypatch.setattr(app_service, "validate_plate_text", lambda value: "66-B1 069.99")

    def fake_vehicle_exit(*args, **kwargs):
        called["saved"] = {"args": args, "kwargs": kwargs}
        return {"success": True, "match_result": "MATCH"}

    monkeypatch.setattr(app_service, "vehicle_exit", fake_vehicle_exit)

    result = app_service.confirm_vehicle_exit(" raw-ticket ", "66b106999", image_path="exit.jpg")

    assert result["success"] is True
    assert called["saved"]["args"][:2] == ("TICKET-1", "66-B1 069.99")


def test_confirm_vehicle_exit_preserves_manual_override_payload(monkeypatch):
    called = {}

    monkeypatch.setattr(app_service, "validate_ticket_id", lambda value: value.strip().upper())
    monkeypatch.setattr(app_service, "validate_plate_text", lambda value: "67-B1 123.45")

    def fake_vehicle_exit(*args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs
        return {"success": True, "match_result": "MISMATCH"}

    monkeypatch.setattr(app_service, "vehicle_exit", fake_vehicle_exit)

    result = app_service.confirm_vehicle_exit(" ticket-9 ", "manual override", image_path="exit.jpg", ocr_confidence=0.42, ocr_text="67B112345", manual_override=True)

    assert result["match_result"] == "MISMATCH"
    assert called["args"][:2] == ("TICKET-9", "67-B1 123.45")
    assert called["kwargs"]["ocr_confidence"] == 0.42
    assert called["kwargs"]["ocr_text"] == "67B112345"
    assert called["kwargs"]["manual_override"] is True
