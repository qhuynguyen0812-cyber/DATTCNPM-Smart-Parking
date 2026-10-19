# Tests Module

## Responsibility

The `tests/` module protects business rules, API contracts, authentication, OCR behavior, storage, migrations, and production readiness.

## Test Categories

- Auth/RBAC tests.
- API contract and response shape tests.
- Parking lifecycle tests.
- OCR/CV quality tests.
- Production readiness tests.
- Storage and database migration tests.
- Streamlit smoke tests.
- Web UI error handling, supported uploads, button retry and permissions.
- Concurrent vehicle entry/exit and exactly-once audit/event records.
- Literal ticket search, nested path redaction and effective AI configuration.

## Rules

- Any business rule change must include tests.
- Any API response shape change must update contract tests.
- Any OCR behavior change must include uncertainty/fusion tests.
- Any production readiness change must update production readiness tests.

## Baseline Command

```powershell
py -3 scripts/run_checks.py
```

Latest verified baseline:

```text
247 backend tests passed; 19 frontend tests passed (2026-10-13).
```

The test runtime database and logs are isolated in a temporary directory before
application modules are imported. Generated sample images can be tested against
the configured provider with `py -3 scripts/run_checks.py --live-vision`.
That opt-in run makes real provider requests and does not create parking tickets.
Synthetic image results are not a field-accuracy estimate.
