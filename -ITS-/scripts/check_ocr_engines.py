import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ocr_engine import list_ocr_engine_statuses


def main():
    for status in list_ocr_engine_statuses():
        print(f"{status.name},{status.available},{status.detail}")


if __name__ == "__main__":
    main()
