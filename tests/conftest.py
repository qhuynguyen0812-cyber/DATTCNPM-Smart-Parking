import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Establish isolation before any application module binds default DB/log paths.
# Domain audit/event functions otherwise use the user's normal runtime database.
_test_runtime = tempfile.TemporaryDirectory(prefix="its-pytest-", ignore_cleanup_errors=True)
os.environ["ITS_BASE_DIR"] = _test_runtime.name
os.environ.setdefault("ITS_FAST_MODE", "true")
os.environ.setdefault("ITS_ENABLE_PADDLE_OCR", "false")
os.environ.setdefault("ITS_ENABLE_HARDCASE_OCR", "false")
os.environ.setdefault("ITS_ENABLE_OPENAI_VISION", "false")
os.environ.setdefault("ITS_OPENAI_API_KEY", "")


def pytest_sessionstart(session):
    from backend.db import init_db
    init_db()
