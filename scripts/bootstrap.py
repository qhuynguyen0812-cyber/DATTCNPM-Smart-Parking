from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = {
    "doctor": [sys.executable, "-m", "scripts.doctor"],
    "test": [sys.executable, "-m", "pytest", "tests", "-q"],
    "api": [sys.executable, "-m", "uvicorn", "api.main:app", "--reload"],
    "web": [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
    "benchmark": [sys.executable, "-m", "scripts.run_benchmark_dataset"],
    "compare-ocr": [sys.executable, "-m", "scripts.compare_ocr_engines"],
    "prepare-ground-truth": [sys.executable, "-m", "scripts.prepare_ground_truth_dataset"],
    "prefill-ground-truth": [sys.executable, "-m", "scripts.prefill_ground_truth"],
    "benchmark-bad": [sys.executable, "-m", "scripts.benchmark_bad_cases"],
    "backup": [sys.executable, "-m", "scripts.backup_runtime"],
    "restore": [sys.executable, "-m", "scripts.restore_runtime"],
    "report": [sys.executable, "-m", "scripts.operational_report"],
    "prod-check": [sys.executable, "-m", "scripts.production_check"],
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python scripts/bootstrap.py [doctor|test|api|web|benchmark|compare-ocr|prepare-ground-truth|prefill-ground-truth|benchmark-bad|backup|restore|report|prod-check]")
        raise SystemExit(1)

    command = COMMANDS[sys.argv[1]]
    print("Running:", " ".join(command))
    raise SystemExit(subprocess.call(command, cwd=ROOT))


if __name__ == "__main__":
    main()
