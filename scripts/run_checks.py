"""Run the backend and browser-logic regression suites with saved reports.

Use --live-vision only when provider calls are explicitly wanted.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "work" / "test-results")
    parser.add_argument("--live-vision", action="store_true")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    xml_path = output / "backend-junit.xml"
    commands = [
        ("backend", [sys.executable, "-m", "pytest", "-q", "--junitxml", str(xml_path)]),
        ("frontend", [shutil.which("node") or "node", "--test", "tests/test_web_ui.cjs", "tests/test_spider_ui.cjs"]),
    ]
    if args.live_vision:
        commands.append(("vision", [sys.executable, "scripts/benchmark_vision_cases.py", "--live", "--output-dir", str(output)]))
    results = {}
    for name, command in commands:
        print("Running " + name + " checks...", flush=True)
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        transcript = process.stdout + process.stderr
        (output / (name + "-output.txt")).write_text(transcript, encoding="utf-8")
        results[name] = {"passed": process.returncode == 0, "exit_code": process.returncode}
        if name == "backend" and xml_path.exists():
            suites = ET.parse(xml_path).getroot()
            results[name]["tests"] = sum(int(suite.attrib.get("tests", 0)) for suite in suites.iter("testsuite"))
        if name == "frontend":
            count = re.search(r"(?:tests|test[s]?)\s+(\d+)", transcript)
            results[name]["tests"] = int(count.group(1)) if count else None
        print(json.dumps({name: results[name]}), flush=True)
    (output / "checks-summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0 if all(row["passed"] for row in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
