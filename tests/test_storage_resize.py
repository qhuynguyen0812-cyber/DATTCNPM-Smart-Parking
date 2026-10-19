from io import BytesIO
from pathlib import Path
import sys

import pytest

pytestmark = pytest.mark.integration


from backend import storage
from backend.validators import MAX_UPLOAD_SIZE_BYTES, ValidationError


class DummyUpload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getbuffer(self):
        return self._data


class DummyFastAPIUpload:
    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self.file = BytesIO(data)


def test_save_uploaded_file_accepts_fastapi_upload(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(storage, "_maybe_resize_for_ocr", lambda buffer, suffix: buffer)

    saved_path = Path(storage.save_uploaded_file(DummyFastAPIUpload("plate.JPG", b"fake-image"), "api entry"))

    assert saved_path.exists()
    assert saved_path.suffix == ".jpg"
    assert saved_path.read_bytes() == b"fake-image"
    assert saved_path.name.startswith("api_entry_")


@pytest.mark.parametrize("filename", ["plate.exe", "plate", ""])
def test_save_uploaded_file_rejects_invalid_extension(tmp_path, monkeypatch, filename):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)

    with pytest.raises(ValidationError, match="Unsupported image format"):
        storage.save_uploaded_file(DummyUpload(filename, b"fake-image"), "entry")


def test_save_uploaded_file_rejects_empty_file(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)

    with pytest.raises(ValidationError, match="Empty upload"):
        storage.save_uploaded_file(DummyUpload("plate.jpg", b""), "entry")


def test_save_uploaded_file_rejects_oversized_file(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)

    with pytest.raises(ValidationError, match="too large"):
        storage.save_uploaded_file(DummyUpload("plate.jpg", b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)), "entry")


def test_save_uploaded_file_sanitizes_prefix_path_separators(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(storage, "_maybe_resize_for_ocr", lambda buffer, suffix: buffer)

    saved_path = Path(storage.save_uploaded_file(DummyUpload("plate.jpg", b"fake"), "../evil/path"))

    assert saved_path.exists()
    assert saved_path.resolve().is_relative_to(tmp_path.resolve())
    assert ".." not in saved_path.name
    assert "/" not in saved_path.name
    assert "\\" not in saved_path.name


def test_save_uploaded_file_preserves_png_suffix(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(storage, "_maybe_resize_for_ocr", lambda buffer, suffix: buffer)

    saved_path = Path(storage.save_uploaded_file(DummyUpload("plate.PNG", b"fake"), "entry"))

    assert saved_path.suffix == ".png"
    assert saved_path.read_bytes() == b"fake"


def test_save_uploaded_file_keeps_raw_bytes_when_cv2_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(storage, "cv2", None)

    saved_path = Path(storage.save_uploaded_file(DummyUpload("plate.jpg", b"not-really-an-image"), "entry"))

    assert saved_path.read_bytes() == b"not-really-an-image"


def test_save_uploaded_file_resizes_large_image(tmp_path, monkeypatch):
    import numpy as np
    import cv2

    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)

    image = np.full((2200, 3200, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode('.jpg', image)
    assert ok

    saved_path = Path(storage.save_uploaded_file(DummyUpload('large.jpg', encoded.tobytes()), 'entry'))
    saved = cv2.imread(str(saved_path))

    assert saved is not None
    assert max(saved.shape[:2]) <= storage.MAX_OCR_INPUT_DIMENSION


def test_save_uploaded_file_keeps_small_image_size(tmp_path, monkeypatch):
    import numpy as np
    import cv2

    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)

    image = np.full((600, 900, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode('.jpg', image)
    assert ok

    saved_path = Path(storage.save_uploaded_file(DummyUpload('small.jpg', encoded.tobytes()), 'entry'))
    saved = cv2.imread(str(saved_path))

    assert saved is not None
    assert saved.shape[0] == 600
    assert saved.shape[1] == 900
