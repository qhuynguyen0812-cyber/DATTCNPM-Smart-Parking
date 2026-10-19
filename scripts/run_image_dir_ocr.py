from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr
from backend.config import REPORT_DIR


def run_image_directory(image_dir: Path, limit: int = 20, ocr_engine: str = "auto") -> dict:
    images = sorted([p for p in image_dir.glob("*.*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}])
    selected = images[:limit] if limit > 0 else images
    samples = []
    latencies = []
    for path in selected:
        start = time.perf_counter()
        try:
            result = run_alpr(str(path), ocr_engine=ocr_engine)
            error = ""
        except Exception as exc:
            result = {"text": "", "confidence": 0.0, "used_ocr": False, "ocr_engine": "error", "quality_note": ""}
            error = str(exc)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)
        samples.append({
            "image": str(path),
            "file": path.name,
            "text": result.get("text", ""),
            "raw_text": result.get("raw_text", ""),
            "confidence": float(result.get("confidence") or 0.0),
            "used_ocr": bool(result.get("used_ocr")),
            "ocr_engine": result.get("ocr_engine", "unknown"),
            "quality_note": result.get("quality_note", ""),
            "detector_label": result.get("detector_label", ""),
            "latency_ms": elapsed,
            "error": error,
        })
    usable = [s for s in samples if s["text"]]
    p95 = 0.0
    if latencies:
        ordered = sorted(latencies)
        p95 = ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]
    return {
        "image_dir": str(image_dir),
        "total_images": len(images),
        "tested_images": len(samples),
        "recognized_count": len(usable),
        "recognized_rate": len(usable) / max(1, len(samples)),
        "average_latency_ms": statistics.mean(latencies) if latencies else 0.0,
        "p95_latency_ms": p95,
        "samples": samples,
    }


def write_reports(payload: dict, report_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "bike_back_real_ocr.json"
    md_path = report_dir / "bike_back_real_ocr.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Bike_back_ctu Real OCR Smoke Report",
        "",
        f"- Image dir: `{payload['image_dir']}`",
        f"- Total images: **{payload['total_images']}**",
        f"- Tested images: **{payload['tested_images']}**",
        f"- Recognized count: **{payload['recognized_count']}**",
        f"- Recognized rate: **{payload['recognized_rate']:.2%}**",
        f"- Average latency: **{payload['average_latency_ms']:.2f} ms**",
        f"- P95 latency: **{payload['p95_latency_ms']:.2f} ms**",
        "",
        "## Samples",
        "",
        "| File | Text | Conf | Engine | Latency ms | Note |",
        "|---|---|---:|---|---:|---|",
    ]
    for s in payload["samples"][:50]:
        lines.append(f"| {s['file']} | {s['text']} | {s['confidence']:.2f} | {s['ocr_engine']} | {s['latency_ms']:.1f} | {s['quality_note'] or s['error']} |")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_dir")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--ocr-engine", default="auto")
    args = parser.parse_args()
    payload = run_image_directory(Path(args.image_dir), limit=args.limit, ocr_engine=args.ocr_engine)
    json_path, md_path = write_reports(payload)
    print("Bike_back real OCR smoke")
    print("=" * 40)
    print(f"Images: {payload['tested_images']} / {payload['total_images']}")
    print(f"Recognized: {payload['recognized_count']} ({payload['recognized_rate']:.2%})")
    print(f"Avg latency: {payload['average_latency_ms']:.2f} ms | P95: {payload['p95_latency_ms']:.2f} ms")
    for sample in payload["samples"][:10]:
        line = f"{sample['file']}: {sample['text']} conf={sample['confidence']:.2f} engine={sample['ocr_engine']} note={sample['quality_note'] or sample['error']}"
        print(line.encode("ascii", errors="replace").decode("ascii"))
    print(f"Reports: {json_path} | {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
