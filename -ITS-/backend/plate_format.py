import re


LETTER_TO_DIGIT = {
    "O": "0",
    "Q": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "B": "8",
}

DIGIT_TO_LETTER = {
    "0": "D",
    "1": "I",
    "2": "Z",
    "5": "S",
    "6": "G",
    "8": "B",
}


def normalize_plate_text(text: str):
    if not text:
        return ""
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return "".join(LETTER_TO_DIGIT.get(ch, ch) for ch in text)


def normalize_vn_top(text: str):
    s = (text or "").upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    if len(s) < 3:
        return s
    chars = list(s)
    for i in range(min(2, len(chars))):
        chars[i] = LETTER_TO_DIGIT.get(chars[i], chars[i])
    if len(chars) >= 3 and chars[2].isdigit():
        chars[2] = DIGIT_TO_LETTER.get(chars[2], chars[2])
    if len(chars) >= 4 and chars[3].isalpha():
        chars[3] = LETTER_TO_DIGIT.get(chars[3], chars[3])
    if len(chars) >= 4 and chars[3].isdigit() and len(chars) >= 5 and chars[4].isalpha():
        chars[4] = LETTER_TO_DIGIT.get(chars[4], chars[4])
    return "".join(chars)


def _format_top_bottom(top_candidate: str, bottom_candidate: str):
    top_candidate = normalize_vn_top(top_candidate)
    bottom_candidate = normalize_plate_text(bottom_candidate)
    if not top_candidate:
        return ""
    if bottom_candidate:
        if re.fullmatch(r"\d{4}", bottom_candidate):
            return f"{top_candidate[:2]}-{top_candidate[2:]} {bottom_candidate}"
        if re.fullmatch(r"\d{5}", bottom_candidate):
            return f"{top_candidate[:2]}-{top_candidate[2:]} {bottom_candidate[:3]}.{bottom_candidate[3:]}"
    return f"{top_candidate[:2]}-{top_candidate[2:]}"


def _extract_top_bottom_candidates(raw: str):
    raw_alnum = re.sub(r"[^A-Z0-9\s.-]", " ", raw)
    line_parts = [p for p in re.split(r"\s+", raw_alnum) if p]
    top_candidate = ""
    bottom_candidate = ""
    for part in line_parts:
        cleaned = part.replace(".", "")
        normalized_top = normalize_vn_top(cleaned)
        if not top_candidate and looks_like_vn_top(normalized_top):
            top_candidate = normalized_top
            continue
        if not bottom_candidate and re.fullmatch(r"\d{2,3}\.?\d{2}", part):
            bottom_candidate = part.replace(".", "")
            continue
        if not bottom_candidate and re.fullmatch(r"\d{4,5}", cleaned):
            bottom_candidate = cleaned
    compact = normalize_plate_text(raw)
    if not top_candidate:
        for size in (5, 4, 3):
            candidate = normalize_vn_top(compact[:size])
            if looks_like_vn_top(candidate):
                top_candidate = candidate
                break
    if top_candidate and not bottom_candidate:
        remain = compact[len(top_candidate):]
        if re.fullmatch(r"\d{4,5}", remain):
            bottom_candidate = remain
    return top_candidate, bottom_candidate


def format_vn_plate(text: str):
    raw = (text or "").upper().strip()
    if not raw:
        return ""
    raw_lines = [re.sub(r"[^A-Z0-9.-]", "", part.upper()) for part in re.split(r"[\r\n]+", raw) if part.strip()]
    if len(raw_lines) >= 2:
        top_line = normalize_vn_top(raw_lines[0].replace("-", ""))
        bottom_line = raw_lines[1].replace(".", "")
        formatted = _format_top_bottom(top_line, bottom_line)
        if formatted and normalize_plate_text(formatted) != normalize_plate_text(top_line):
            return formatted
    top_candidate, bottom_candidate = _extract_top_bottom_candidates(raw)
    if top_candidate:
        return _format_top_bottom(top_candidate, bottom_candidate)
    return normalize_plate_text(raw)


def combine_vn_two_line(top_text: str, bottom_text: str):
    top = normalize_vn_top(top_text)
    bottom = normalize_plate_text(bottom_text)
    top_patterns = (
        r"\d{2}[A-Z]\d",
        r"\d{2}[A-Z]{2}",
        r"\d{2}[A-Z]{2}\d",
    )
    for pattern in top_patterns:
        if re.fullmatch(pattern, top):
            if re.fullmatch(r"\d{4}", bottom):
                return f"{top[:2]}-{top[2:]} {bottom}"
            if re.fullmatch(r"\d{5}", bottom):
                return f"{top[:2]}-{top[2:]} {bottom[:3]}.{bottom[3:]}"
    return ""


def candidate_bottoms(bottom_text: str):
    raw = (bottom_text or "").upper()
    s = normalize_plate_text(raw)
    if not s:
        return []
    candidates = [s]
    if len(s) == 4:
        candidates.append(s[:3] + "0" + s[3:])
        candidates.append(s[:2] + "0" + s[2:])
    if len(s) == 5 and s[0] == "1":
        candidates.append("5" + s[1:])
    if len(s) >= 1:
        swap_map = {"1": ["5", "7"], "5": ["1", "6"], "6": ["5", "8"], "8": ["3", "6"], "3": ["8"]}
        first = s[0]
        for rep in swap_map.get(first, []):
            candidates.append(rep + s[1:])
    for ch, rep in LETTER_TO_DIGIT.items():
        if ch in raw:
            candidates.append(normalize_plate_text(raw.replace(ch, rep)))
    if len(s) == 4:
        candidates.extend(["0" + s, s + "0"])
    return list(dict.fromkeys(candidates))


def looks_like_vn_top(text: str):
    s = normalize_vn_top(text)
    return bool(re.fullmatch(r"\d{2}[A-Z]", s) or re.fullmatch(r"\d{2}[A-Z]{2}", s) or re.fullmatch(r"\d{2}[A-Z]\d", s) or re.fullmatch(r"\d{2}[A-Z]{2}\d", s))


def looks_like_vn_bottom(text: str):
    s = normalize_plate_text(text)
    return bool(re.fullmatch(r"\d{4}", s) or re.fullmatch(r"\d{5}", s) or re.fullmatch(r"\d{3}\d{2}", s))


def is_top_only_plate(text: str):
    s = (text or "").strip().upper()
    normalized = normalize_vn_top(s)
    return bool(
        re.fullmatch(r"\d{2}-[A-Z]\d", s)
        or re.fullmatch(r"\d{2}[A-Z]\d", normalized)
        or re.fullmatch(r"\d{2}[A-Z]{2}", normalized)
        or re.fullmatch(r"\d{2}[A-Z]{2}\d", normalized)
    )
