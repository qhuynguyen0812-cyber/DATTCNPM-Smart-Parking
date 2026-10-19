# API Module

## Responsibility

The `api/` module exposes the backend through FastAPI. It should remain a thin HTTP boundary over application/domain services.

## Files

- `main.py` — FastAPI app, routes, dependencies, response mapping.
- `schemas.py` — Pydantic response schemas.

## Rules

- Do not duplicate business logic here.
- Call `backend.app_service` and `backend.parking_service` for operations.
- Enforce authentication and RBAC on all non-public routes.
- Use `ok()` / `error_payload()` response shape consistently.
- Sanitize local filesystem paths before returning API responses.

## Public Endpoints

- `/health`
- `/readiness`
- `/metrics`

## Secured Capabilities

- OCR upload.
- Vehicle entry/exit.
- Active tickets.
- Logs/events.
- Review resolution.
- Admin user management.
- Device status/barrier command.

## Security Notes

- Mutating routes must call `enforce_write_rate_limit()`.
- Admin routes require `admin`.
- Write operations require `admin` or `operator`.
- Read operations allow `admin`, `operator`, `viewer`.
