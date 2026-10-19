import re
from dataclasses import dataclass

from backend.plate_format import format_vn_plate, looks_like_vn_bottom, looks_like_vn_top, normalize_plate_text


MIN_CONFIDENCE_FOR_USABLE_OCR = 0.45
STRONG_CONFIDENCE_FOR_USABLE_OCR = 0.70


@dataclass(frozen=True)
class OcrQualityAssessment:
    is_usable: bool
    quality_note: str
    normalized_text: str
    formatted_text: str


FULL_VN_PATTERNS = (
    re.compile(r"\d{2}[A-Z]\d{4,5}"),
    re.compile(r"\d{2}[A-Z]{2}\d{4}"),
    re.compile(r"\d{2}[A-Z]{2}\d{5}"),
)


def clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def is_full_vn_plate(normalized_text: str) -> bool:
    return any(pattern.fullmatch(normalized_text) for pattern in FULL_VN_PATTERNS)


def assess_ocr_quality(text: str, confidence: float) -> OcrQualityAssessment:
    formatted = format_vn_plate(text)
    normalized = normalize_plate_text(formatted)
    conf = clamp_confidence(confidence)

    if not normalized:
        return OcrQualityAssessment(False, "Không có ký tự hợp lệ", normalized, formatted)

    if is_full_vn_plate(normalized):
        if conf >= MIN_CONFIDENCE_FOR_USABLE_OCR:
            return OcrQualityAssessment(True, "Biển số hợp lệ", normalized, formatted)
        return OcrQualityAssessment(False, "Đúng định dạng nhưng confidence thấp", normalized, formatted)

    if looks_like_vn_top(normalized) or looks_like_vn_bottom(normalized):
        return OcrQualityAssessment(False, "Mới đọc được một phần biển số", normalized, formatted)

    if conf >= STRONG_CONFIDENCE_FOR_USABLE_OCR and len(normalized) >= 7:
        return OcrQualityAssessment(True, "OCR mạnh nhưng chưa khớp hoàn toàn định dạng", normalized, formatted)

    if len(normalized) >= 7 and conf >= 0.60:
        return OcrQualityAssessment(True, "Kết quả gần đúng, chấp nhận cho kiểm tra thủ công", normalized, formatted)

    return OcrQualityAssessment(False, "Kết quả OCR chưa đủ tin cậy", normalized, formatted)
