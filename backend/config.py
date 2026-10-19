import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def _load_env_file_fallback(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_ENV_PATH = Path(__file__).resolve().parents[1] / '.env'
if load_dotenv is not None:
    load_dotenv(_ENV_PATH)
else:
    _load_env_file_fallback(_ENV_PATH)


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


APP_TITLE = os.getenv("ITS_APP_TITLE", "Hệ thống nhận diện biển số xe máy")
SCHEMA_VERSION = 2

BASE_DIR = _ensure_dir(Path(os.getenv("ITS_BASE_DIR", str(Path.home() / "plate_demo_data"))))
DB_PATH = BASE_DIR / os.getenv("ITS_DB_NAME", "parking_system.db")
UPLOAD_DIR = _ensure_dir(BASE_DIR / os.getenv("ITS_UPLOAD_DIR", "uploads"))
LOG_DIR = _ensure_dir(BASE_DIR / os.getenv("ITS_LOG_DIR", "logs"))
REPORT_DIR = _ensure_dir(BASE_DIR / os.getenv("ITS_REPORT_DIR", "reports"))

DEFAULT_MODEL_LABEL = os.getenv("ITS_DEFAULT_MODEL_LABEL", "Baseline detector")
FAST_MODE = _as_bool(os.getenv("ITS_FAST_MODE"), default=True)
API_TOKEN = os.getenv("ITS_API_TOKEN", "")
API_JWT_SECRET = os.getenv("ITS_API_JWT_SECRET", "dev-only-change-me")
API_JWT_EXPIRE_MINUTES = int(os.getenv("ITS_API_JWT_EXPIRE_MINUTES", "120"))
API_ALLOW_STATIC_TOKENS = _as_bool(os.getenv("ITS_API_ALLOW_STATIC_TOKENS"), default=True)
LOG_LEVEL = os.getenv("ITS_LOG_LEVEL", "INFO")
ENABLE_PADDLE_OCR = _as_bool(os.getenv("ITS_ENABLE_PADDLE_OCR"), default=False)
ENABLE_HARDCASE_OCR = _as_bool(os.getenv("ITS_ENABLE_HARDCASE_OCR"), default=False)
OCR_ACCURACY_MODE = _as_bool(os.getenv("ITS_OCR_ACCURACY_MODE"), default=True)
ENABLE_DEEP_OCR_RETRY = _as_bool(os.getenv("ITS_ENABLE_DEEP_OCR_RETRY"), default=True)
DEEP_OCR_CONFIDENCE_THRESHOLD = float(os.getenv("ITS_DEEP_OCR_CONFIDENCE_THRESHOLD", "0.86" if OCR_ACCURACY_MODE else "0.80"))
ENABLE_PADDLE_FALLBACK = _as_bool(os.getenv("ITS_ENABLE_PADDLE_FALLBACK"), default=OCR_ACCURACY_MODE)
ENABLE_OPENAI_VISION = _as_bool(os.getenv("ITS_ENABLE_OPENAI_VISION"), default=False)
OPENAI_API_KEY = os.getenv("ITS_OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("ITS_OPENAI_BASE_URL", "")
OPENAI_VISION_MODEL = os.getenv("ITS_OPENAI_VISION_MODEL", "gpt-4.1-mini")
OPENAI_API_MODE = os.getenv("ITS_OPENAI_API_MODE", "responses")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("ITS_OPENAI_TIMEOUT_SECONDS", "45"))
ENABLE_VISION_IN_AUTO = _as_bool(os.getenv("ITS_ENABLE_VISION_IN_AUTO"), default=OCR_ACCURACY_MODE)
BENCHMARK_UPLOADS_DIR = Path(os.getenv("ITS_BENCHMARK_UPLOADS_DIR", str(UPLOAD_DIR)))

STREAMLIT_AUTH_ENABLED = _as_bool(os.getenv("ITS_STREAMLIT_AUTH_ENABLED"), default=True)
STREAMLIT_ADMIN_USERNAME = os.getenv("ITS_STREAMLIT_ADMIN_USERNAME", "admin")
STREAMLIT_ADMIN_PASSWORD = os.getenv("ITS_STREAMLIT_ADMIN_PASSWORD", "")
STREAMLIT_OPERATOR_USERNAME = os.getenv("ITS_STREAMLIT_OPERATOR_USERNAME", "operator")
STREAMLIT_OPERATOR_PASSWORD = os.getenv("ITS_STREAMLIT_OPERATOR_PASSWORD", "")
STREAMLIT_VIEWER_USERNAME = os.getenv("ITS_STREAMLIT_VIEWER_USERNAME", "viewer")
STREAMLIT_VIEWER_PASSWORD = os.getenv("ITS_STREAMLIT_VIEWER_PASSWORD", "")

API_BEARER_TOKENS = {
    "admin": os.getenv("ITS_API_BEARER_ADMIN_TOKEN", ""),
    "operator": os.getenv("ITS_API_BEARER_OPERATOR_TOKEN", ""),
    "viewer": os.getenv("ITS_API_BEARER_VIEWER_TOKEN", ""),
}
API_EXPOSE_INTERNAL_PATHS = _as_bool(os.getenv("ITS_API_EXPOSE_INTERNAL_PATHS"), default=False)
