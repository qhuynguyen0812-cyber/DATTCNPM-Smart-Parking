from pathlib import Path

import pytest

from backend import storage

pytestmark = pytest.mark.unit


class DummyCameraImage:
    name = "camera.jpg"

    def getbuffer(self):
        return b"fake-camera-image"


def test_save_uploaded_file_accepts_camera_input(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(storage, "_maybe_resize_for_ocr", lambda buffer, suffix: buffer)

    saved_path = Path(storage.save_uploaded_file(DummyCameraImage(), "entry_camera"))

    assert saved_path.exists()
    assert saved_path.parent == tmp_path
    assert saved_path.suffix == ".jpg"
    assert saved_path.read_bytes() == b"fake-camera-image"


def test_save_uploaded_file_sanitizes_prefix_path_separators(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(storage, "_maybe_resize_for_ocr", lambda buffer, suffix: buffer)

    saved_path = Path(storage.save_uploaded_file(DummyCameraImage(), "../evil"))

    assert saved_path.exists()
    assert saved_path.parent == tmp_path
    assert ".." not in saved_path.name
    assert "/" not in saved_path.name
    assert "\\" not in saved_path.name
