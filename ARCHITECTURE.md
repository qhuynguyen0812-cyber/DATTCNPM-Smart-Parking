# ITS Parking System Architecture

## Purpose

This project is an Intelligent Transportation System parking application for motorcycle license plate recognition, ticket lifecycle management, operator review, auditability, and future hardware integration.

## Architecture Style

The implementation follows a layered modular architecture:

```text
Frontend UI Layer
  -> Application Service Layer
    -> Domain / Business Service Layer
      -> OCR / CV Service Layer
      -> Persistence Layer
      -> Integration Adapter Layer
API Layer parallels the Frontend and calls the same application/domain services.
```

## Module Map

| Module | Path | Responsibility | Documentation |
|---|---|---|---|
| API | `api/` | FastAPI contracts, auth dependencies, HTTP response shape | [api/MODULE.md](api/MODULE.md) |
| Backend | `backend/` | Business logic, auth, persistence, OCR, validation | [backend/MODULE.md](backend/MODULE.md) |
| Frontend | `frontend/` | Streamlit operator/admin UI | [frontend/MODULE.md](frontend/MODULE.md) |
| Integrations | `integrations/` | Camera, MQTT, barrier adapters/simulators | [integrations/MODULE.md](integrations/MODULE.md) |
| Models | `models/` | Detector model weights and model notes | [models/MODULE.md](models/MODULE.md) |
| Scripts | `scripts/` | Diagnostics, benchmark, production utilities | [scripts/README.md](scripts/README.md) |
| Tests | `tests/` | Unit/contract/regression coverage | [tests/MODULE.md](tests/MODULE.md) |
| Docs | `docs/` | Business, production, hardware, architecture docs | [docs/MODULE.md](docs/MODULE.md) |
| Agent Context | `.agents/` | Agent instructions, skills, and project context | [.agents/README.md](.agents/README.md) |

## Core Business Flow

### Vehicle Entry

```text
Image upload/camera snapshot
-> OCR/CV recognition
-> operator confirms plate or manual override
-> create active ticket
-> audit event
```

### Vehicle Exit

```text
Exit image upload/camera snapshot
-> OCR/CV recognition
-> compare against active ticket entry plate
-> if match: complete ticket
-> if mismatch: route to NEEDS_REVIEW
-> audit event
```

### Review Resolution

```text
Review ticket
-> operator/admin selects resolution
-> approve, correct, or reject
-> close ticket / update records
-> audit event
```

## Accuracy-First OCR/CV Policy

The project prioritizes factual correctness over speed.

Primary OCR:

```text
ChatGPT 5.5 Vision via 9Router
```

Detector priority:

```text
models/external/sourudra-model2.pt
models/external/sourudra-model1.pt
models/external/sourudra-another_model.pt
baseline fallback
```

Local OCR engines remain fallback/diagnostic only.

## Security Model

- PBKDF2 password hashing.
- Login lockout.
- Signed bearer/session tokens.
- Role-based access control:
  - `admin`
  - `operator`
  - `viewer`
- Write endpoint rate limiting.
- Upload extension/content-type validation.
- Internal path redaction by default.
- Audit logs for sensitive operations.

## Missing / Open Production Items

- Real hardware endpoint values are not yet available:

```env
ITS_CAMERA_URL=
ITS_MQTT_URL=
ITS_BARRIER_URL=
```

- Simulator mode is valid for demo/staging, not final field production.
- Field production requires camera, MQTT, and barrier controller credentials.

## Verification Baseline

Latest verified state:

```text
Full test suite: 172 passed
Production demo check: pass=10 warn=1 fail=0
Warn: hardware simulator mode due to missing real hardware endpoints
```
