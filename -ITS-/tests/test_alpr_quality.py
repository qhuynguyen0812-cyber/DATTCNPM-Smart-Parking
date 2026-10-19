from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ocr_quality import assess_ocr_quality


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
    assert "confidence thấp" in assessment.quality_note.lower()


def test_borderline_readable_plate_is_usable_for_manual_review():
    assessment = assess_ocr_quality("91-B2 152.30", 0.61)
    assert assessment.is_usable is True
