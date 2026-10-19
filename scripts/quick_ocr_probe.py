import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr
from backend.config import BENCHMARK_UPLOADS_DIR


def main():
    files = sorted(BENCHMARK_UPLOADS_DIR.glob("*.jpg"))[:8]
    rows = []
    for image_path in files:
        result = run_alpr(str(image_path))
        rows.append(
            {
                "file": image_path.name,
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "is_usable": result.get("is_usable", False),
                "quality_note": result.get("quality_note", ""),
            }
        )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
