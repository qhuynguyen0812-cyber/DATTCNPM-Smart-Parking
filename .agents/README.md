# Agent Context for ITS Parking System

## Mission

Maintain and extend an accuracy-first parking management system for motorcycle license plate recognition.

## Non-Negotiable Principles

1. Correct plate identification is more important than speed.
2. Never claim OCR is factually correct just because the format is valid.
3. Do not expose API keys, JWT secrets, local filesystem paths, or device credentials.
4. Preserve auditability for entry, exit, review, account, and barrier actions.
5. Keep UI, API, and backend business rules aligned.
6. Do not fake production readiness by inventing hardware endpoints.

## Current Primary OCR Strategy

Use 9Router with model:

```text
cx/gpt-6-sol
```

Config:

```env
ITS_ENABLE_OPENAI_VISION=true
ITS_ENABLE_VISION_IN_AUTO=true
ITS_OPENAI_BASE_URL=http://localhost:20128/v1
ITS_OPENAI_VISION_MODEL=cx/gpt-6-sol
```

## Known Missing Production Inputs

```env
ITS_CAMERA_URL=
ITS_MQTT_URL=
ITS_BARRIER_URL=
```

Do not guess these. Ask the user or discover them only through safe, authorized local inspection.

## Recommended Workflow for Agents

1. Read [ARCHITECTURE.md](../ARCHITECTURE.md).
2. Read the relevant module `MODULE.md`.
3. Check [docs/BUSINESS_RULES.md](../docs/BUSINESS_RULES.md).
4. Make minimal targeted changes.
5. Run targeted tests.
6. Run full suite when changing business logic, auth, OCR, or API contracts.
7. Update docs if module boundaries or business rules change.

## Verification Commands

```powershell
python -m pytest -q
python scripts\production_check.py --demo-ok
python scripts\cv_doctor.py
```
