import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alpr_service import run_alpr


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: python scripts/run_alpr_check.py <image_path> <output_json>")

    image_path = sys.argv[1]
    output_json = sys.argv[2]
    result = run_alpr(image_path)
    Path(output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_json)


if __name__ == "__main__":
    main()
