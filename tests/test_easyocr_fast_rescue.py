import pytest

pytestmark = pytest.mark.ocr


from backend.alpr_service import EasyOCRVNOCR


def test_needs_rescue_for_empty_text():
    helper = object.__new__(EasyOCRVNOCR)
    assert helper._needs_rescue_ocr("", 0.0, 1.5, True) is True


def test_needs_rescue_for_vertical_borderline_case():
    helper = object.__new__(EasyOCRVNOCR)
    assert helper._needs_rescue_ocr("68-P6 6255", 0.92, 1.1, True) is True


def test_no_rescue_for_strong_horizontal_plate():
    helper = object.__new__(EasyOCRVNOCR)
    assert helper._needs_rescue_ocr("66-B1 069.99", 0.95, 2.8, False) is False
