import re
from pathlib import Path

from backend.config import DEFAULT_MODEL_LABEL, FAST_MODE
from backend.ocr_quality import assess_ocr_quality
from backend.plate_format import (
    candidate_bottoms,
    combine_vn_two_line,
    format_vn_plate,
    is_top_only_plate,
    looks_like_vn_bottom,
    looks_like_vn_top,
    normalize_plate_text,
    normalize_vn_top,
)
from backend.storage import save_annotated_image

try:
    import cv2
except Exception:
    cv2 = None

try:
    import easyocr
except Exception:
    easyocr = None

try:
    from fast_alpr import ALPR
    from fast_alpr.alpr import BaseOCR, OcrResult
except Exception:
    ALPR = None
    BaseOCR = object
    OcrResult = None


def repair_vn_top(text: str):
    s = normalize_vn_top(text)
    if re.fullmatch(r"\d{2}[A-Z]", s) or re.fullmatch(r"\d{2}[A-Z]{2}", s) or re.fullmatch(r"\d{2}[A-Z]\d", s) or re.fullmatch(r"\d{2}[A-Z]{2}\d", s):
        return s
    if len(s) >= 3 and s[:2].isdigit():
        tail = s[2:]
        if not tail:
            return s
        first = tail[0]
        fix_map = {"8": "B", "6": "G", "0": "D", "2": "Z", "5": "S"}
        fixed = fix_map.get(first, first)
        candidate = s[:2] + fixed + tail[1:]
        if re.fullmatch(r"\d{2}[A-Z]", candidate) or re.fullmatch(r"\d{2}[A-Z]{2}", candidate) or re.fullmatch(r"\d{2}[A-Z]\d", candidate) or re.fullmatch(r"\d{2}[A-Z]{2}\d", candidate):
            return candidate
    return s


def repair_vn_bottom(text: str):
    s = normalize_plate_text(text)
    if re.fullmatch(r"\d{5}", s):
        return s
    if re.fullmatch(r"\d{4}", s):
        return s[:3] + "0" + s[3:]
    if len(s) == 5:
        sub_map = {"B": "8", "S": "5", "Z": "2", "G": "6", "I": "1", "L": "1", "O": "0", "D": "0"}
        repaired = "".join(sub_map.get(ch, ch) for ch in s)
        if re.fullmatch(r"\d{5}", repaired):
            return repaired
    return s


def score_full_plate(text: str, conf: float):
    norm = normalize_plate_text(text)
    if not norm:
        return -999.0
    score = conf * 100.0
    if re.fullmatch(r"\d{2}[A-Z]\d{5}", norm):
        score += 260
    elif re.fullmatch(r"\d{2}[A-Z]{2}\d{4}", norm):
        score += 255
    elif re.fullmatch(r"\d{2}[A-Z]{2}\d{5}", norm):
        score += 260
    elif re.fullmatch(r"\d{2}[A-Z]\d{4,5}", norm):
        score += 180
    elif looks_like_vn_top(norm):
        score += 60
    elif looks_like_vn_bottom(norm):
        score += 40
    if 6 <= len(norm) <= 9:
        score += 45
    elif len(norm) <= 3:
        score -= 50
    if any(ch.isalpha() for ch in norm[4:]):
        score -= 35
    if len(norm) >= 2 and not norm[:2].isdigit():
        score -= 60
    return score




class EasyOCRVNOCR(BaseOCR):
    def __init__(self) -> None:
        if easyocr is None:
            raise RuntimeError("easyocr is not installed")
        self.reader = easyocr.Reader(["en"], gpu=False)

    def _enhance(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        blur = cv2.bilateralFilter(gray, 5, 35, 35)
        sharp = cv2.addWeighted(gray, 1.6, blur, -0.6, 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(sharp)
        _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
        variants = [("clahe", clahe), ("otsu", otsu)]
        if not FAST_MODE:
            variants.extend([("adaptive", adaptive), ("morph", morph), ("sharp", sharp)])
        return variants

    def _ocr_candidates(self, image):
        if image is None or image.size == 0:
            return []
        candidates = []
        for _, variant in self._enhance(image):
            try:
                rows = self.reader.readtext(
                    variant,
                    detail=1,
                    paragraph=False,
                    batch_size=1,
                    decoder="greedy",
                    allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-",
                    width_ths=0.7,
                    link_threshold=0.2,
                    text_threshold=0.55,
                    low_text=0.3,
                )
            except Exception:
                rows = []
            if rows:
                line_text = " ".join(item[1].strip() for item in rows if len(item) >= 3 and item[1].strip())
                if line_text:
                    line_conf = sum(float(item[2]) for item in rows if len(item) >= 3) / max(1, len(rows))
                    candidates.append((line_text, line_conf))
            for row in rows:
                if len(row) >= 3:
                    _, text, conf = row
                    candidates.append((text.strip(), float(conf)))
        dedup = {}
        for text, conf in candidates:
            norm = normalize_plate_text(text)
            if not norm:
                continue
            score = score_full_plate(text, conf)
            if norm not in dedup or score > dedup[norm][0]:
                dedup[norm] = (score, text, conf)
        sorted_rows = sorted(dedup.values(), key=lambda x: (x[0], x[2]), reverse=True)
        return [(text, conf) for _, text, conf in sorted_rows]

    def _ocr_best(self, image):
        candidates = self._ocr_candidates(image)
        if not candidates:
            return "", 0.0
        best_text, best_conf = candidates[0]
        return best_text, best_conf

    def _split_vertical_plate(self, image, top_ratio=0.52, overlap_ratio=0.34, top_trim=0.08):
        h, w = image.shape[:2]
        if h <= 0 or w <= 0:
            return image, image
        top_cut = int(h * top_trim)
        base = image[top_cut:, :] if top_cut < h else image
        hh, _ = base.shape[:2]
        top = base[: max(1, int(hh * top_ratio)), :]
        bottom = base[max(0, int(hh * overlap_ratio)) :, :]
        return top, bottom

    def _combine_from_candidates(self, top_rows, bottom_rows):
        top_candidates = [(text, conf) for text, conf in top_rows[:6] if looks_like_vn_top(text)] or top_rows[:4]
        bottom_candidates = [(text, conf) for text, conf in bottom_rows[:8] if looks_like_vn_bottom(text)] or bottom_rows[:5]
        best = ("", 0.0)
        for t_text, t_conf in top_candidates:
            repaired_top = repair_vn_top(t_text)
            for b_text, b_conf in bottom_candidates:
                bottom_pool = candidate_bottoms(b_text) + candidate_bottoms(repair_vn_bottom(b_text))
                for bottom_candidate in dict.fromkeys(bottom_pool):
                    combined = combine_vn_two_line(repaired_top, bottom_candidate)
                    if not combined:
                        continue
                    combined_norm = normalize_plate_text(combined)
                    score = (t_conf + b_conf) / 2.0
                    if looks_like_vn_top(repaired_top) and looks_like_vn_bottom(bottom_candidate):
                        score += 0.10
                    if len(combined_norm) >= 8:
                        score += 0.05
                    if re.fullmatch(r'\d{2}[A-Z]{2}\d{4}', combined_norm):
                        score += 0.08
                    if re.fullmatch(r'\d{2}[A-Z]\d{5}', combined_norm) or re.fullmatch(r'\d{2}[A-Z]{2}\d{5}', combined_norm):
                        score += 0.08
                    if score > best[1]:
                        best = (combined, min(0.999, score))
        return best

    def predict(self, cropped_plate):
        if cropped_plate is None:
            return None

        h, w = cropped_plate.shape[:2]
        ratio = w / max(h, 1)

        if ratio >= 2.2:
            text, conf = self._ocr_best(cropped_plate)
            text = format_vn_plate(text)
            return OcrResult(text=text, confidence=conf) if text else None

        split_configs = [
            (0.52, 0.34, 0.08),
            (0.48, 0.30, 0.03),
            (0.56, 0.38, 0.10),
        ]
        best_combo = ("", 0.0)
        last_bottom_rows = []
        for top_ratio, overlap_ratio, top_trim in split_configs:
            top, bottom = self._split_vertical_plate(cropped_plate, top_ratio=top_ratio, overlap_ratio=overlap_ratio, top_trim=top_trim)
            top_rows = self._ocr_candidates(top)
            bottom_rows = self._ocr_candidates(bottom)
            last_bottom_rows = bottom_rows
            combined_text, combined_conf = self._combine_from_candidates(top_rows, bottom_rows)
            if combined_conf > best_combo[1]:
                best_combo = (combined_text, combined_conf)
        if best_combo[0]:
            return OcrResult(text=best_combo[0], confidence=best_combo[1])

        full_text, full_conf = self._ocr_best(cropped_plate)
        full_text = format_vn_plate(full_text)
        if full_text and not (is_top_only_plate(full_text) and last_bottom_rows and any(looks_like_vn_bottom(t) for t, _ in last_bottom_rows[:4])):
            return OcrResult(text=full_text, confidence=full_conf)

        if FAST_MODE:
            return OcrResult(text=full_text, confidence=full_conf) if full_text else None

        top, bottom = self._split_vertical_plate(cropped_plate, top_ratio=0.50, overlap_ratio=0.28, top_trim=0.0)
        extra_top_rows = self._ocr_candidates(top) + self._ocr_candidates(cv2.resize(top, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC))
        extra_bottom_rows = self._ocr_candidates(bottom) + self._ocr_candidates(cv2.resize(bottom, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC))
        combined_text, combined_conf = self._combine_from_candidates(extra_top_rows, extra_bottom_rows)
        if combined_text:
            return OcrResult(text=combined_text, confidence=combined_conf)

        return OcrResult(text=full_text, confidence=full_conf) if full_text else None


def get_detector_choices(external_model_dir: Path):
    choices = [(DEFAULT_MODEL_LABEL, None)]
    for model_path in sorted(external_model_dir.glob("*.pt")):
        choices.append((f"External: {model_path.name}", str(model_path)))
    return choices


def load_fast_alpr(model_path: str | None = None):
    if ALPR is None or easyocr is None:
        return None
    try:
        kwargs = {"ocr": EasyOCRVNOCR()}
        if model_path:
            kwargs["detector_model"] = model_path
        return ALPR(**kwargs)
    except TypeError:
        try:
            kwargs = {"ocr": EasyOCRVNOCR()}
            if model_path:
                kwargs["model_path"] = model_path
            return ALPR(**kwargs)
        except Exception:
            return None
    except Exception:
        return None


def run_alpr(image_path: str, detector_model: str | None = None):
    if cv2 is None:
        return {"text": "", "confidence": 0.0, "message": "OpenCV unavailable", "used_ocr": False, "annotated_path": image_path}

    alpr = load_fast_alpr(detector_model)
    if alpr is None:
        missing = []
        if ALPR is None:
            missing.append("fast-alpr")
        if easyocr is None:
            missing.append("easyocr")
        return {
            "text": "",
            "confidence": 0.0,
            "message": f"Thiếu {', '.join(missing)}",
            "used_ocr": False,
            "annotated_path": image_path,
            "detector_label": DEFAULT_MODEL_LABEL if not detector_model else Path(detector_model).name,
        }

    frame = cv2.imread(image_path)
    if frame is None:
        return {"text": "", "confidence": 0.0, "message": "Invalid image", "used_ocr": False, "annotated_path": image_path, "detector_label": DEFAULT_MODEL_LABEL if not detector_model else Path(detector_model).name}

    try:
        drawn = alpr.draw_predictions(frame)
        results = drawn.results or []
        annotated_path = save_annotated_image(cv2, drawn.image, "alpr")
    except Exception:
        try:
            results = alpr.predict(image_path) or []
        except Exception:
            results = []
        annotated_path = image_path

    if not results:
        return {
            "text": "",
            "confidence": 0.0,
            "message": "OCR failed",
            "used_ocr": False,
            "annotated_path": annotated_path,
            "detector_label": DEFAULT_MODEL_LABEL if not detector_model else Path(detector_model).name,
            "raw_text": "",
            "is_usable": False,
            "quality_note": "Không có kết quả OCR",
        }

    best = sorted(
        results,
        key=lambda x: getattr(getattr(x, "ocr", None), "confidence", 0.0) or 0.0,
        reverse=True,
    )[0]

    ocr = getattr(best, "ocr", None)
    detection = getattr(best, "detection", None)
    raw_text = getattr(ocr, "text", "") or ""
    text = format_vn_plate(raw_text)
    conf = float(getattr(ocr, "confidence", 0.0) or 0.0)
    det_conf = float(getattr(detection, "confidence", 0.0) or 0.0)

    detector_label = DEFAULT_MODEL_LABEL if not detector_model else Path(detector_model).name
    assessment = assess_ocr_quality(text or raw_text, conf)
    return {
        "text": text,
        "confidence": conf,
        "message": f"{detector_label} • fast-alpr (det {det_conf:.2f}) • {assessment.quality_note}",
        "used_ocr": bool(text),
        "annotated_path": annotated_path,
        "detector_label": detector_label,
        "raw_text": raw_text,
        "is_usable": assessment.is_usable,
        "quality_note": assessment.quality_note,
        "normalized_text": assessment.normalized_text,
    }

