# Production Audit

## Executive Summary

The ITS Parking project has been cleaned and audited for production readiness. Core business flows are implemented and covered by tests. The application is structurally sound for a demo/staging environment, with two production blockers remaining before real field deployment:

1. Replace default JWT secret.
2. Configure real hardware/device credentials instead of simulator mode.

## Repository Organization

Current professional structure:

```text
api/              FastAPI HTTP layer and schemas
backend/          Business logic, auth, OCR, persistence, validation
frontend/         Native Streamlit UI
integrations/     Camera, barrier, MQTT/device adapters
models/           External detector weights
scripts/          Operational, benchmark, and maintenance utilities
tests/            Automated test suite
docs/             Requirements, reports, and archived references
data/             Benchmark/sample data
tools/            Reserved for active developer tools
```

Cleanup completed:

- Removed unused legacy exact-HTML imports from `frontend/app.py`.
- Archived legacy UI mockups to `docs/archive/ui_mockups/`.
- Archived iframe migration tools to `docs/archive/migration_tools/`.
- Removed local Python/test cache folders.
- Added `scripts/README.md` to classify operational utilities.

## Business Logic Coverage

| Feature | Status | Notes |
|---|---:|---|
| Login/logout | PASS | Streamlit auth and API bearer sessions available |
| Role-based access | PASS | `admin`, `operator`, `viewer` |
| Vehicle entry | PASS | Creates active `IN_PARKING` ticket |
| Vehicle exit | PASS | Completes ticket on matching plate |
| Mismatch review | PASS | Mismatch creates/requires review path |
| Resolve ticket | PASS | Operator/admin resolution supported |
| Cancel ticket | PASS | API admin-only |
| Logs | PASS | UI/API log visibility available |
| Audit logs | PASS | Admin-only API access |
| Accounts | PASS | Admin user create/update/disable/delete |
| OCR primary | PASS | 9Router `cx/gpt-5.5` Vision configured as primary OCR |
| OCR fallback | PASS | Local OCR/Paddle remain fallback/diagnostic |

## Security Review

Implemented controls:

- PBKDF2 password hashing.
- Login lockout after repeated failures.
- Password policy for new users.
- Signed bearer/session tokens.
- RBAC for read/write/admin endpoints.
- Write rate limiting for mutating API routes.
- Upload extension and content-type validation.
- API path sanitization unless explicitly enabled.
- Audit log/event trail for operational changes.

Production blockers from `production_check.py`:

| Check | Result | Required Action |
|---|---:|---|
| JWT secret | FAIL | Set strong `ITS_API_JWT_SECRET` |
| Hardware mode | FAIL | Configure real device credentials for field deployment |
| Static tokens | WARN | Disable or restrict for production |

Recommended production `.env` hardening:

```env
ITS_API_JWT_SECRET=<long-random-secret>
ITS_API_ALLOW_STATIC_TOKENS=false
ITS_API_EXPOSE_INTERNAL_PATHS=false
ITS_STREAMLIT_ADMIN_PASSWORD=<strong-password>
```

## API / Frontend Parity

| UI Area | Backend/API Support |
|---|---|
| Dashboard | `/operations/summary`, `/logs`, service metrics |
| Xe vào | `/vehicle/entry`, `confirm_vehicle_entry()` |
| Xe ra | `/vehicle/exit`, `confirm_vehicle_exit()` |
| Review | `/tickets/{ticket_id}/resolve`, `resolve_review_ticket()` |
| Logs | `/logs`, `/events`, audit logs |
| Accounts | `/admin/users`, role/active/delete endpoints |
| OCR | `/ocr`, `process_plate_image()` |
| Devices | `/devices/status`, `/devices/barrier/open` |

## OCR / CV Setup

Accuracy-first configuration is active:

```env
ITS_FAST_MODE=false
ITS_OCR_ACCURACY_MODE=true
ITS_ENABLE_OPENAI_VISION=true
ITS_ENABLE_VISION_IN_AUTO=true
ITS_OPENAI_BASE_URL=http://localhost:20128/v1
ITS_OPENAI_VISION_MODEL=cx/gpt-5.5
ITS_ENABLE_PADDLE_FALLBACK=true
```

Detector priority:

1. `models/external/sourudra-model2.pt`
2. `models/external/sourudra-model1.pt`
3. `models/external/sourudra-another_model.pt`
4. baseline fallback

## Verification Results

### Production Check

```txt
PASS: 8
WARN: 1
FAIL: 2
```

Failures are environment/deployment issues, not code regressions:

- Default JWT secret.
- Simulator hardware mode.

### CV Doctor

```txt
PASS: OpenCV, fast-alpr, EasyOCR, PaddleOCR installed, PaddleOCR fallback,
      accuracy mode, external models, full OCR enhancement, OpenAI Vision.
WARN: PaddleOCR primary engine disabled.
```

PaddleOCR warning is acceptable because GPT-5.5 Vision is the primary OCR.

### Tests

```txt
172 passed in 16.38s
```

### Syntax Check

```txt
python -m py_compile api/main.py backend/*.py frontend/app.py frontend/ui.py
PASS
```

## Remaining Production Actions

Before real deployment:

1. Set `ITS_API_JWT_SECRET` to a strong secret.
2. Set `ITS_API_ALLOW_STATIC_TOKENS=false` unless legacy token access is required.
3. Configure real camera/barrier/MQTT credentials.
4. Restart Streamlit and API services after `.env` changes.
5. Perform one field test with real entry/exit images and a real operator account.
