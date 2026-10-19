from backend.alpr_service import repair_vn_bottom
from backend.ocr_quality import assess_ocr_quality
from backend.plate_format import format_vn_plate


def test_repair_vn_bottom_preserves_legacy_four_digit_plate():
    assert repair_vn_bottom("5505") == "5505"


def test_format_vn_plate_supports_legacy_four_digit_plate():
    assert format_vn_plate("65X35505") == "65-X3 5505"


def test_assess_ocr_quality_accepts_legacy_four_digit_plate_when_confident():
    assessment = assess_ocr_quality("65-X3 5505", 0.95)
    assert assessment.is_usable is True
    assert assessment.formatted_text == "65-X3 5505"
