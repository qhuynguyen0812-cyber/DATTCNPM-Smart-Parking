import pytest

pytestmark = pytest.mark.ocr


from backend import hardcase_ocr


def test_external_detector_candidate_can_upgrade_partial_baseline():
    baseline = {"text": "66-B1", "confidence": 0.72, "is_usable": False}
    candidate = {
        "text": "66-B1 069.99",
        "confidence": 0.83,
        "is_usable": True,
        "variant": "detector:model.pt",
    }

    assert hardcase_ocr._candidate_is_safe_upgrade(baseline, candidate) is True


def test_non_upgrade_variant_is_rejected():
    baseline = {"text": "66-B1", "confidence": 0.72, "is_usable": False}
    candidate = {
        "text": "66-B1 069.99",
        "confidence": 0.99,
        "is_usable": True,
        "variant": "raw",
    }

    assert hardcase_ocr._candidate_is_safe_upgrade(baseline, candidate) is False
