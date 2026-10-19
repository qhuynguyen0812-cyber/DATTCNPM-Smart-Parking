import numpy as np
import pytest

from backend import alpr_service

pytestmark = pytest.mark.unit


def test_auto_mode_fuses_openai_vision_candidate(monkeypatch, tmp_path):
    image_path = tmp_path / "plate.jpg"
    image_path.write_bytes(b"fake")
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    monkeypatch.setattr(alpr_service, "cv2", type("FakeCV2", (), {"imread": staticmethod(lambda path: fake_frame)})())
    monkeypatch.setattr(alpr_service, "load_fast_alpr", lambda detector_model=None: None)
    monkeypatch.setattr(alpr_service, "_run_paddle_ocr", lambda *args, **kwargs: None)
    monkeypatch.setattr(alpr_service, "ENABLE_OPENAI_VISION", True)
    monkeypatch.setattr(alpr_service, "ENABLE_VISION_IN_AUTO", True)
    monkeypatch.setattr(alpr_service, "OCR_ACCURACY_MODE", True)
    monkeypatch.setattr(
        alpr_service,
        "run_openai_vision",
        lambda path: {
            "text": "60-U1 463.20",
            "raw_text": "60-U1 463.20",
            "confidence": 0.8,
            "is_usable": True,
            "quality_note": "Biển số hợp lệ",
            "normalized_text": "60U146320",
            "formatted_text": "60-U1 463.20",
        },
    )

    result = alpr_service.run_alpr(str(image_path), ocr_engine="auto")

    assert result["text"] == "60-U1 463.20"
    assert result["ocr_engine"] == "vision-fusion"
    assert "openai-vision" in result["fusion_sources"]


def test_auto_mode_marks_vision_disagreement(monkeypatch, tmp_path):
    image_path = tmp_path / "plate.jpg"
    image_path.write_bytes(b"fake")
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    monkeypatch.setattr(alpr_service, "cv2", type("FakeCV2", (), {"imread": staticmethod(lambda path: fake_frame)})())
    monkeypatch.setattr(alpr_service, "ENABLE_OPENAI_VISION", True)
    monkeypatch.setattr(alpr_service, "ENABLE_VISION_IN_AUTO", True)
    monkeypatch.setattr(alpr_service, "OCR_ACCURACY_MODE", True)
    monkeypatch.setattr(alpr_service, "_run_paddle_ocr", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        alpr_service,
        "run_openai_vision",
        lambda path: {
            "text": "60-U1 463.20",
            "raw_text": "60-U1 463.20",
            "confidence": 0.8,
            "is_usable": True,
            "quality_note": "Biển số hợp lệ",
            "normalized_text": "60U146320",
            "formatted_text": "60-U1 463.20",
        },
    )
    monkeypatch.setattr(
        alpr_service,
        "load_fast_alpr",
        lambda detector_model=None: type(
            "FakeALPR",
            (),
            {
                "draw_predictions": lambda self, frame: type(
                    "Drawn",
                    (),
                    {
                        "image": frame,
                        "results": [
                            type(
                                "Result",
                                (),
                                {
                                    "ocr": type("OCR", (), {"text": "60-D1 163.20", "confidence": 0.99})(),
                                    "detection": type("Det", (), {"confidence": 0.9})(),
                                },
                            )()
                        ],
                    },
                )(),
            },
        )(),
    )
    monkeypatch.setattr(alpr_service, "save_annotated_image", lambda cv2, image, prefix: str(image_path))

    result = alpr_service.run_alpr(str(image_path), ocr_engine="auto")

    assert result["vision_disagreement"] is True
    assert result["ocr_engine"] == "vision-fusion"
    assert "không thống nhất" in result["quality_note"]
