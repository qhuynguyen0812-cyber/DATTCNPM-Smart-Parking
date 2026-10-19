# Agent Skills

## Skill: Business Rule Safe Change

Use when modifying ticket lifecycle, roles, audit logs, or review behavior.

Checklist:

- Identify affected business rule in `docs/BUSINESS_RULES.md`.
- Update backend service first.
- Update API contract if exposed over HTTP.
- Update frontend labels/actions.
- Add or update tests.
- Run full test suite.

## Skill: OCR Accuracy Change

Use when changing `backend/alpr_service.py`, OCR adapters, or OCR UI display.

Checklist:

- Keep GPT-6 Sol Vision via 9Router as primary OCR unless user says otherwise.
- Keep local OCR engines as fallback/diagnostic.
- Do not display fake accuracy/latency claims.
- Use uncertainty wording: `Đúng định dạng`, `Cần đối chiếu ảnh`, `Cần rà tay`.
- Flag engine disagreement instead of hiding it.

## Skill: Security Change

Use when changing auth, API, `.env`, tokens, upload, or role handling.

Checklist:

- Never print secrets.
- Keep static tokens disabled in production.
- Keep internal paths hidden unless explicitly enabled.
- Preserve admin-only user management.
- Preserve write rate limiting.
- Add tests for new auth behavior.

## Skill: Hardware Integration Change

Use when adding camera, MQTT, or barrier integration.

Checklist:

- Do not fake hardware URLs.
- Keep simulator mode safe for demo.
- Require explicit endpoint config for production pass.
- Document required credentials in `docs/HARDWARE_CONFIGURATION.md`.
- Verify `/devices/status` contract.
