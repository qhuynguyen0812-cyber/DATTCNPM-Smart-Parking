"""Configure server-side AI credentials without echoing keys or changing other settings."""
import argparse
from getpass import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from backend.ai_settings import save_ai_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check configuration without sending an image")
    args = parser.parse_args()
    if args.check:
        from backend.openai_vision_adapter import vision_configuration_status
        result = vision_configuration_status()
        print("Model:", result["model"])
        print("Cấu hình:", "đủ" if result["configured"] else "thiếu " + ", ".join(result["missing"]))
        print("Kết nối AI chưa được xác minh bằng ảnh thực.")
        return 0 if result["configured"] else 1
    base_url = input("Base URL [http://localhost:20128/v1]: ").strip() or "http://localhost:20128/v1"
    model = input("Model [cx/gpt-6-sol]: ").strip() or "cx/gpt-6-sol"
    mode = input("Loại API responses/chat [responses]: ").strip() or "responses"
    key = getpass("Khóa API (ẩn khi nhập): ").strip()
    save_ai_config(ROOT / ".env", api_key=key, base_url=base_url, model=model, api_mode=mode)
    print("Đã lưu cấu hình AI. Khởi động lại Streamlit/API để áp dụng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
