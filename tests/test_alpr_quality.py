import pytest

from backend.ocr_quality import assess_ocr_quality, clamp_confidence


def test_usable_for_valid_vn_plate_with_good_confidence():
    assessment = assess_ocr_quality("66-B1 069.99", 0.88)
    assert assessment.is_usable is True
    assert assessment.quality_note == "Biển số hợp lệ"


def test_not_usable_for_partial_plate():
    assessment = assess_ocr_quality("66-B1", 0.95)
    assert assessment.is_usable is False
    assert "một phần" in assessment.quality_note.lower()


def test_not_usable_for_low_confidence_full_plate():
    assessment = assess_ocr_quality("66-B1 069.99", 0.2)
    assert assessment.is_usable is False
    assert "confidence" in assessment.quality_note.lower()


def test_borderline_readable_plate_is_not_usable_when_confidence_is_too_low():
    assessment = assess_ocr_quality("91-B2 152.30", 0.61)
    assert assessment.is_usable is False
    assert "confidence" in assessment.quality_note.lower() or "tin cậy" in assessment.quality_note.lower()


def test_full_plate_can_still_be_usable_for_manual_review_when_confidence_is_high_enough():
    assessment = assess_ocr_quality("91-B2 152.30", 0.80)
    assert assessment.is_usable is True


def test_dotted_five_digit_plate_needs_higher_confidence_floor():
    assessment = assess_ocr_quality("73-D5 613.45", 0.727)
    assert assessment.is_usable is False
    assert "confidence" in assessment.quality_note.lower()


def test_numeric_only_string_is_not_usable_even_with_high_confidence():
    assessment = assess_ocr_quality("35433233", 0.92)
    assert assessment.is_usable is False
    assert "thiếu ký tự chữ" in assessment.quality_note.lower()


@pytest.mark.parametrize(
    "confidence, expected",
    [
        (0.72, True),
        (0.719, False),
    ],
)
def test_full_plate_confidence_boundary(confidence, expected):
    assert assess_ocr_quality("66-B1 0699", confidence).is_usable is expected


@pytest.mark.parametrize(
    "confidence, expected",
    [
        (0.75, True),
        (0.749, False),
    ],
)
def test_dotted_five_digit_confidence_boundary(confidence, expected):
    assert assess_ocr_quality("66-B1 069.99", confidence).is_usable is expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        (1.7, 1.0),
        (-0.5, 0.0),
        (0.42, 0.42),
    ],
)
def test_clamp_confidence_bounds(raw, expected):
    assert clamp_confidence(raw) == expected
