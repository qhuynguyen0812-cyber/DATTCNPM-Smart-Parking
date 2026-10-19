from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app


def main() -> int:
    client = TestClient(app)
    checks = [
        ("GET", "/health", None, (200,)),
        ("GET", "/readiness", None, (200,)),
        ("GET", "/system/scorecard", None, (200,)),
        ("GET", "/operations/summary", None, (401, 503)),
        ("GET", "/ai/status", None, (401,)),
        ("GET", "/logs", None, (401, 503)),
    ]
    ok = True
    for method, path, kwargs, expected in checks:
        response = getattr(client, method.lower())(path, **(kwargs or {}))
        passed = response.status_code in expected
        ok = ok and passed
        print(f"[{'PASS' if passed else 'FAIL'}] {method} {path}: {response.status_code}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
