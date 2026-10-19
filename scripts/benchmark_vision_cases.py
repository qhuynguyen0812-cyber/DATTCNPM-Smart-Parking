"""Run 12 reproducible synthetic image cases through the configured AI adapter.

This diagnostic sends only generated test images and never creates parking tickets.
It is opt-in; it is not executed by pytest and may consume provider usage.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from backend import config
from backend.openai_vision_adapter import run_openai_vision, _redact_secrets


def plate(lines, background="white"):
    image = Image.new("RGB", (600, 300), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, 588, 288), radius=14, outline="black", width=6)
    font_path = Path("C:/Windows/Fonts/arialbd.ttf")
    if not font_path.exists():
        raise RuntimeError("Set a suitable bold font for synthetic image generation")
    if len(lines) == 1:
        font = ImageFont.truetype(str(font_path), 65)
        draw.text((300, 150), lines[0], font=font, anchor="mm", fill="black")
    else:
        font = ImageFont.truetype(str(font_path), 98)
        draw.text((300, 82), lines[0], font=font, anchor="mm", fill="black")
        draw.text((300, 205), lines[1], font=font, anchor="mm", fill="black")
    return image


def build_cases(folder):
    base = plate(["59-B1", "069.99"])
    blocked = base.copy()
    ImageDraw.Draw(blocked).rectangle((180, 140, 590, 280), fill="#444444")
    double = Image.new("RGB", (1200, 340), "#64748b")
    double.paste(base, (0, 20))
    double.paste(plate(["67-C2", "123.45"]), (600, 20))
    cases = [
        ("motorcycle_clear", base, "59B106999", False),
        ("car_one_line", plate(["30F-513.15"]), "30F51315", False),
        ("legacy_four_digits", plate(["59-B1", "1234"]), "59B11234", False),
        ("yellow_plate", plate(["51D-246.80"], "#ffde52"), "51D24680", False),
        ("rotated_10_degrees", base.rotate(10, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="#6b7280"), "59B106999", False),
        ("dark_image", ImageEnhance.Brightness(base).enhance(.35), "59B106999", False),
        ("mild_blur", base.filter(ImageFilter.GaussianBlur(1.5)), "59B106999", False),
        ("small_image", base.resize((210, 105), Image.Resampling.LANCZOS), "59B106999", False),
        ("no_plate", Image.new("RGB", (600, 300), "#64748b"), "", True),
        ("multiple_plates", double, "", True),
        ("covered_digits", blocked, "", True),
        ("unreadable_blur", base.filter(ImageFilter.GaussianBlur(24)), "", True),
    ]
    result = []
    for name, image, expected, abstain in cases:
        path = folder / (name + ".png")
        image.save(path)
        result.append(dict(name=name, path=path, expected=expected, abstain=abstain))
    return result


def run_case(case):
    started = time.perf_counter()
    try:
        result = run_openai_vision(str(case["path"]))
        recognized = result.get("text", "")
        compact = ''.join(ch for ch in recognized.upper() if ch.isalnum())
        passed = (not result.get("is_usable") and not compact) if case["abstain"] else compact == case["expected"]
        return dict(name=case["name"], expected=case["expected"], expect_abstention=case["abstain"],
                    recognized=recognized, passed=passed, is_usable=result.get("is_usable"),
                    review_required=result.get("review_required"), analysis=result.get("ai_analysis"),
                    seconds=round(time.perf_counter() - started, 2))
    except Exception as exc:
        return dict(name=case["name"], expected=case["expected"], expect_abstention=case["abstain"],
                    passed=False, error=_redact_secrets(exc), seconds=round(time.perf_counter() - started, 2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2, choices=[1, 2])
    parser.add_argument("--live", action="store_true", help="Explicitly opt in to configured provider requests")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    samples = args.output_dir / "synthetic-images"
    samples.mkdir(exist_ok=True)
    cases = build_cases(samples)
    if not args.live:
        print("Generated 12 cases. Add --live to send the generated images to the configured provider.")
        return 0
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_case, case) for case in cases]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ("name", "passed", "recognized", "seconds", "error")}, ensure_ascii=False), flush=True)
    ordered = {case["name"]: i for i, case in enumerate(cases)}
    results.sort(key=lambda row: ordered[row["name"]])
    summary = dict(model=config.OPENAI_VISION_MODEL, synthetic_only=True,
                   passed=sum(row["passed"] for row in results), total=len(results), cases=results)
    (args.output_dir / "vision-benchmark.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("model", "passed", "total", "synthetic_only")}), flush=True)
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
