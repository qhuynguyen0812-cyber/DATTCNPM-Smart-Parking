from pathlib import Path

import numpy as np
import pytest

from backend import alpr_service

pytestmark = pytest.mark.unit


def test_openai_vision_requested_raises_instead_of_silent_fallback(monkeypatch, tmp_path):
    image_path = tmp_path / "plate.jpg"
    image_path.write_bytes(b"fake")

    monkeypatch.setattr(alpr_service, "ENABLE_OPENAI_VISION", True)
    monkeypatch.setattr(alpr_service, "run_openai_vision", lambda path: (_ for _ in ()).throw(RuntimeError("boom")))
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    monkeypatch.setattr(alpr_service, "cv2", type("FakeCV2", (), {"imread": staticmethod(lambda path: fake_frame)})())
    monkeypatch.setattr(alpr_service, "load_fast_alpr", lambda detector_model=None: None)

    with pytest.raises(RuntimeError, match="OpenAI vision failed"):
        alpr_service.run_alpr(str(image_path), ocr_engine="openai-vision")
