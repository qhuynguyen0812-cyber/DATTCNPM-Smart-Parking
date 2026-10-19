import pytest

from backend.validators import ValidationError, validate_image_extension, validate_plate_text, validate_ticket_id, validate_upload_size


def test_validate_image_extension_accepts_png():
    assert validate_image_extension("plate.png") == ".png"


def test_validate_image_extension_rejects_exe():
    with pytest.raises(ValidationError):
        validate_image_extension("virus.exe")


def test_validate_upload_size_rejects_empty():
    with pytest.raises(ValidationError):
        validate_upload_size(0)


def test_validate_ticket_id_rejects_blank():
    with pytest.raises(ValidationError):
        validate_ticket_id("   ")


def test_validate_plate_text_rejects_blank():
    with pytest.raises(ValidationError):
        validate_plate_text("")


def test_validate_plate_text_accepts_full_vn_plate():
    assert validate_plate_text("66b106999") == "66-B1 069.99"


def test_validate_plate_text_rejects_incomplete_plate():
    with pytest.raises(ValidationError):
        validate_plate_text("66B1")
