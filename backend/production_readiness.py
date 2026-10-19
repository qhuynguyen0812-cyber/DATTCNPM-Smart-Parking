from dataclasses import dataclass
from pathlib import Path
import sqlite3

from backend.config import API_ALLOW_STATIC_TOKENS, API_JWT_SECRET, BASE_DIR, DB_PATH, LOG_DIR, REPORT_DIR, UPLOAD_DIR
from integrations.device_config import load_device_config


@dataclass(frozen=True)
class ReadinessFinding:
    name: str
    status: str
    detail: str


def check_production_readiness(*, demo_ok: bool = False) -> list[ReadinessFinding]:
    findings: list[ReadinessFinding] = []
    default_secret = API_JWT_SECRET == "dev-only-change-me"
    secret_too_short = len(API_JWT_SECRET) < 32
    secret_weak = default_secret or secret_too_short
    findings.append(ReadinessFinding(
        "jwt_secret",
        "warn" if secret_weak and demo_ok else ("fail" if secret_weak else "pass"),
        "JWT secret is default or too short (< 32 chars); set a strong ITS_API_JWT_SECRET" if secret_weak else "JWT secret configured",
    ))
    findings.append(ReadinessFinding(
        "static_tokens",
        "warn" if API_ALLOW_STATIC_TOKENS else "pass",
        "Static tokens enabled for backward-compatible demo mode" if API_ALLOW_STATIC_TOKENS else "Static tokens disabled",
    ))
    for name, path in [("base_dir", BASE_DIR), ("upload_dir", UPLOAD_DIR), ("log_dir", LOG_DIR), ("report_dir", REPORT_DIR)]:
        findings.append(ReadinessFinding(name, "pass" if Path(path).exists() else "fail", f"{path}"))
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("SELECT 1")
        findings.append(ReadinessFinding("database_writable", "pass", str(DB_PATH)))
    except Exception as exc:
        findings.append(ReadinessFinding("database_writable", "fail", str(exc)))
    for report_name in ["benchmark_report.md", "evaluation_report.md", "performance_smoke.md"]:
        report_path = REPORT_DIR / report_name
        findings.append(ReadinessFinding(report_name, "pass" if report_path.exists() else "warn", str(report_path)))
    config = load_device_config()
    if config.mode == "READY_FOR_REAL_DEVICE":
        findings.append(ReadinessFinding(
            "hardware_mode",
            "pass",
            "Real hardware endpoints configured for camera, MQTT, and barrier integrations.",
        ))
    else:
        findings.append(ReadinessFinding(
            "hardware_mode",
            "warn" if demo_ok else "fail",
            "Simulator mode. Missing real hardware credentials: " + ", ".join(config.missing),
        ))
    return findings


def summarize_findings(findings: list[ReadinessFinding]) -> dict[str, int]:
    return {
        "pass": sum(1 for item in findings if item.status == "pass"),
        "warn": sum(1 for item in findings if item.status == "warn"),
        "fail": sum(1 for item in findings if item.status == "fail"),
    }
