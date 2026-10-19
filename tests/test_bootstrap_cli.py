from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_backup_entrypoint_does_not_import_fail():
    result = subprocess.run(
        [sys.executable, "scripts/bootstrap.py", "backup"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert "ModuleNotFoundError" not in result.stderr
    assert result.returncode == 0
