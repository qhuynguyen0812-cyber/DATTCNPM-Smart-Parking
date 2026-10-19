from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import DB_PATH
from backend.db import fetch_logs, init_db, list_app_users
from backend.parking_metrics import build_parking_kpis, classify_operational_health


@dataclass
class ValidationIssue:
    severity: str
    code: str
    message: str


def validate_runtime_db(db_path=DB_PATH) -> list[ValidationIssue]:
    init_db(db_path)
    issues: list[ValidationIssue] = []
    logs = fetch_logs(db_path)

    if not logs.empty:
        if {"status", "exit_time"}.issubset(logs.columns):
            bad_completed = logs[(logs["status"] == "COMPLETED") & (logs["exit_time"].isna() | (logs["exit_time"].astype(str).str.strip() == ""))]
            if not bad_completed.empty:
                issues.append(ValidationIssue("error", "COMPLETED_WITHOUT_EXIT_TIME", f"{len(bad_completed)} completed tickets missing exit_time"))
            bad_active = logs[(logs["status"] == "IN_PARKING") & logs["exit_time"].notna() & (logs["exit_time"].astype(str).str.strip() != "")]
            if not bad_active.empty:
                issues.append(ValidationIssue("error", "ACTIVE_WITH_EXIT_TIME", f"{len(bad_active)} active tickets unexpectedly have exit_time"))
        if {"status", "review_reason", "match_result"}.issubset(logs.columns):
            bad_review = logs[(logs["status"] == "NEEDS_REVIEW") & (logs["match_result"] != "MISMATCH") & (logs["review_reason"].isna() | (logs["review_reason"].astype(str).str.strip() == ""))]
            if not bad_review.empty:
                issues.append(ValidationIssue("warning", "REVIEW_WITHOUT_REASON", f"{len(bad_review)} review tickets missing reason"))

    users = list_app_users(db_path)
    if not users.empty and "role" in users.columns:
        invalid_roles = users[~users["role"].isin(["admin", "operator", "viewer"])]
        if not invalid_roles.empty:
            issues.append(ValidationIssue("error", "INVALID_USER_ROLE", f"{len(invalid_roles)} users have invalid roles"))

    return issues


def main() -> int:
    issues = validate_runtime_db()
    kpis = build_parking_kpis(fetch_logs())
    health_code, health_tone = classify_operational_health(kpis)
    print("Runtime DB validation")
    print("=" * 40)
    print(f"Health: {health_code} ({health_tone})")
    print(f"Tickets: total={kpis.total_tickets}, active={kpis.active_tickets}, review={kpis.review_tickets}, completed={kpis.completed_tickets}, cancelled={kpis.cancelled_tickets}")
    if not issues:
        print("[OK] No runtime DB issues found")
        return 0
    for issue in issues:
        print(f"[{issue.severity.upper()}] {issue.code}: {issue.message}")
    return 1 if any(issue.severity == "error" for issue in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
