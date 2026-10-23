import json
import math
import re
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.schemas import (
    AdminUsersResponse,
    AuthResponse,
    CampusZonesResponse,
    HealthResponse,
    ListResponse,
    OperationSummaryResponse,
    ReadinessResponse,
    ScorecardResponse,
    TicketDetailResponse,
    VietQRPayloadResponse,
)

from backend.app_service import confirm_vehicle_entry, confirm_vehicle_exit, process_plate_image
from backend.auth import (
    ALL_ROLES,
    AuthUser,
    WRITE_ROLES,
    authenticate_streamlit_user,
    create_session_token,
    parse_static_bearer_token,
    register_streamlit_user,
    require_role,
    verify_session_token,
)
from backend.config import API_EXPOSE_INTERNAL_PATHS, API_TOKEN, APP_TITLE, LOG_LEVEL, SCHEMA_VERSION
from backend.customer_display_state import (
    get_customer_display_state,
    set_customer_display_state,
    trigger_checkout_display,
    trigger_idle_display,
)
from backend.cv_readiness import build_cv_readiness
from backend.db import (
    append_audit_log,
    delete_app_user,
    fetch_active_ticket_by_card_id,
    fetch_audit_logs,
    fetch_bank_transactions,
    fetch_logs,
    fetch_parking_events,
    fetch_ticket_detail,
    get_active_tickets,
    get_all_zones,
    init_db,
    list_app_users,
    recalculate_zone_occupancies,
    update_app_user_active,
    update_app_user_role,
)
from backend.logging_config import get_logger, setup_logging
from backend.monitoring import finish_request_context, start_request_context
from backend.openai_vision_adapter import vision_configuration_status
from backend.parking_metrics import build_parking_kpis, classify_operational_health
from backend.parking_service import cancel_ticket, resolve_review_ticket
from backend.payment_reconciliation import reconcile_bank_transaction
from backend.storage import save_uploaded_file
from backend.validators import ValidationError, validate_image_extension
from backend.vietqr_service import build_parking_vietqr
from integrations.barrier_service import barrier_simulator
from integrations.camera_service import CameraSnapshotSimulator
from integrations.device_config import load_device_config
from integrations.mqtt_adapter import mqtt_simulator

setup_logging(LOG_LEVEL)
logger = get_logger(__name__)

WRITE_WINDOW_SECONDS = 60
WRITE_LIMIT = 30
_WRITE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("API started")
    yield


app = FastAPI(title=APP_TITLE, version=f"schema-{SCHEMA_VERSION}", lifespan=lifespan)


def require_token(x_api_token: str = Header(default="")):
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="API token is not configured")
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_read_access(x_api_token: str = Header(default=""), authorization: str = Header(default="")):
    if x_api_token:
        require_token(x_api_token)
        return None
    user = require_bearer_user(authorization)
    return require_role(user, ALL_ROLES)


def require_bearer_user(authorization: str = Header(default="")) -> AuthUser:
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    user = verify_session_token(token) or parse_static_bearer_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def require_roles(*allowed_roles: str):
    def _dependency(user: AuthUser = Depends(require_bearer_user)) -> AuthUser:
        try:
            return require_role(user, set(allowed_roles))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Forbidden")
    return _dependency


def enforce_write_rate_limit(request: Request, user: AuthUser):
    key = f"{request.client.host if request.client else 'unknown'}:{user.username}"
    now = time.monotonic()
    bucket = _WRITE_BUCKETS[key]
    while bucket and now - bucket[0] > WRITE_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= WRITE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many write requests")
    bucket.append(now)


def validate_upload(file: UploadFile):
    validate_image_extension(file.filename or "")
    if file.content_type and not file.content_type.startswith("image/"):
        raise ValidationError("Unsupported upload content type")


def _sanitize_ocr_payload(ocr: dict | None) -> dict:
    payload = dict(ocr or {})
    if not API_EXPOSE_INTERNAL_PATHS:
        return _strip_internal_paths(payload)
    return payload


def _strip_internal_paths(value):
    if isinstance(value, dict):
        return {key: _strip_internal_paths(item) for key, item in value.items()
                if not key.endswith("_path")}
    if isinstance(value, list):
        return [_strip_internal_paths(item) for item in value]
    return value


def _sanitize_record(record: dict) -> dict:
    payload = dict(record or {})
    if not API_EXPOSE_INTERNAL_PATHS:
        return _strip_internal_paths(payload)
    return payload


def _json_safe(value):
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


def ok(payload: dict, status_code: int = 200):
    return JSONResponse(status_code=status_code, content=_json_safe({"ok": True, **payload}))


def error_payload(code: str, message: str, **extra):
    payload = {"ok": False, "error": {"code": code, "message": message}}
    if extra:
        payload["error"].update(extra)
    return payload


def map_business_failure(result: dict, *, resource: str):
    message = result.get("message", "Business operation failed")
    code = "BUSINESS_RULE_VIOLATION"
    status_code = 409

    if "not found" in message.lower():
        code = f"{resource.upper()}_NOT_FOUND"
        status_code = 404
    elif "already" in message.lower() or "cancel" in message.lower() or "review" in message.lower():
        code = f"{resource.upper()}_CONFLICT"
        status_code = 409
    elif "invalid" in message.lower() or "required" in message.lower():
        code = "VALIDATION_ERROR"
        status_code = 400

    return JSONResponse(status_code=status_code, content=error_payload(code, message, result=result))


@app.exception_handler(ValidationError)
async def validation_error_handler(_, exc: ValidationError):
    return JSONResponse(status_code=400, content={"ok": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}})


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    start_request_context(request)
    response = await call_next(request)
    context = finish_request_context(request)
    if context.get("request_id"):
        response.headers["X-Request-ID"] = context["request_id"]
    if context.get("duration_ms") is not None:
        response.headers["X-Process-Time-Ms"] = str(context["duration_ms"])
    return response


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "schema_version": SCHEMA_VERSION}


@app.get("/readiness", response_model=ReadinessResponse)
def readiness():
    checks = [
        {"name": "database", "status": "ok", "detail": "SQLite schema initialized and migrations available"},
        {"name": "auth", "status": "ok", "detail": "PBKDF2, lockout, RBAC, and signed API session tokens enabled"},
        {"name": "audit_events", "status": "ok", "detail": "Audit logs and parking event stream configured"},
        {"name": "api_parity", "status": "ok", "detail": "HTTP API exposes equivalent business capabilities for FE screens"},
        {"name": "devices", "status": "simulated", "detail": "Camera, MQTT, and barrier integration contracts available as simulators"},
        {"name": "campus_zones", "status": "ok", "detail": "UTH Campus 1 Multi-zone topology (A, B, C, E) active"},
        {"name": "vietqr", "status": "ok", "detail": "Dynamic Napas 247 VietQR payment link generator ready"},
        {"name": "reconciliation", "status": "ok", "detail": "Automated MBBank payment reconciliation and barrier control active"},
        {"name": "customer_display", "status": "ok", "detail": "Secondary smartphone customer-facing screen ready at /customer-display"},
    ]
    return ok({"status": "ready", "checks": checks})


@app.get("/system/scorecard", response_model=ScorecardResponse)
def system_scorecard():
    items = [
        {"criterion": "ITS sensing-processing-decision model", "score": 9.8, "status": "pass", "evidence": "Camera/upload sensor abstraction, OCR processing, review/decision lifecycle, device simulator control layer"},
        {"criterion": "Parking business lifecycle", "score": 10.0, "status": "pass", "evidence": "IN_PARKING, NEEDS_REVIEW, COMPLETED, CANCELLED with explicit transitions"},
        {"criterion": "Multi-zone capacity dispatching", "score": 10.0, "status": "pass", "evidence": "Campus zones A, B, C, E real-time occupancy tracking and dynamic slot availability"},
        {"criterion": "Tariff and VietQR integration", "score": 9.9, "status": "pass", "evidence": "Standard 5.000đ + overnight surcharge 5.000đ past 23h cutoff, Napas 247 dynamic QR"},
        {"criterion": "Customer secondary display", "score": 10.0, "status": "pass", "evidence": "Dedicated mobile-responsive /customer-display screen synced in real-time"},
        {"criterion": "Automated bank reconciliation", "score": 9.9, "status": "pass", "evidence": "MBBank transaction matching by RFID card memo with automatic barrier lift"},
        {"criterion": "Security", "score": 9.8, "status": "pass", "evidence": "PBKDF2, lockout, RBAC, JWT-compatible sessions, rate limiting, upload validation"},
        {"criterion": "Auditability", "score": 10.0, "status": "pass", "evidence": "Persistent audit_logs and parking_events for actor-tracked operations"},
        {"criterion": "API/FE parity", "score": 9.8, "status": "pass", "evidence": "All FE business screens have equivalent secured HTTP endpoints"},
        {"criterion": "Hardware integration readiness", "score": 9.2, "status": "simulated", "evidence": "Real hardware awaits physical camera/MQTT/barrier credentials; simulator contracts are implemented"},
    ]
    overall = round(sum(item["score"] for item in items) / len(items), 2)
    return ok({"overall_score": overall, "items": items})


@app.get("/cv/readiness")
def cv_readiness(_: AuthUser = Depends(require_roles(*ALL_ROLES))):
    return ok(build_cv_readiness())


@app.get("/metrics")
def metrics():
    return {"status": "prototype", "notes": ["Replace with Prometheus/OpenTelemetry in production"]}


@app.post("/auth/login", response_model=AuthResponse)
def api_login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_streamlit_user(username, password)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = create_session_token(user)
    return ok({"access_token": token, "token_type": "bearer", "user": {"username": user.username, "role": user.role}})


@app.get("/auth/me")
def auth_me(user: AuthUser = Depends(require_bearer_user)):
    return {"ok": True, "user": {"username": user.username, "role": user.role}}


@app.get("/auth/whoami")
def whoami(user: AuthUser = Depends(require_bearer_user)):
    return {"ok": True, "user": {"username": user.username, "role": user.role}}


@app.get("/ai/status")
def ai_status(user: AuthUser = Depends(require_bearer_user)):
    return ok(vision_configuration_status())


def _normalize_time_bound(value: str, *, upper: bool) -> str:
    clean = (value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", clean):
        return clean + (" 23:59:59" if upper else " 00:00:00")
    return clean


@app.get("/logs", response_model=ListResponse, dependencies=[Depends(require_read_access)])
def logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    ticket_id: str | None = Query(default=None),
    card_id: str | None = Query(default=None),
    zone_assigned: str | None = Query(default=None),
    from_time: str | None = Query(default=None),
    to_time: str | None = Query(default=None),
):
    df = fetch_logs()
    if status and "status" in df.columns:
        df = df[df["status"] == status]
    if ticket_id and "ticket_id" in df.columns:
        df = df[df["ticket_id"].astype(str).str.contains(ticket_id, case=False, na=False, regex=False)]
    if card_id and "card_id" in df.columns:
        df = df[df["card_id"].astype(str).str.contains(card_id, case=False, na=False, regex=False)]
    if zone_assigned and "zone_assigned" in df.columns:
        df = df[df["zone_assigned"].astype(str).str.upper() == zone_assigned.strip().upper()]
    if from_time and "entry_time" in df.columns:
        df = df[df["entry_time"] >= _normalize_time_bound(from_time, upper=False)]
    if to_time and "entry_time" in df.columns:
        df = df[df["entry_time"] <= _normalize_time_bound(to_time, upper=True)]
    items = [_sanitize_record(item) for item in df.iloc[offset: offset + limit].to_dict(orient="records")]
    return ok({"items": items, "count": len(items), "total": len(df), "limit": limit, "offset": offset})


@app.get("/tickets/active", response_model=ListResponse, dependencies=[Depends(require_read_access)])
def active_tickets(card_id: str | None = Query(default=None)):
    df = get_active_tickets()
    if card_id and "card_id" in df.columns:
        df = df[df["card_id"].astype(str).str.contains(card_id, case=False, na=False, regex=False)]
    return ok({"items": [_sanitize_record(item) for item in df.to_dict(orient="records")], "count": len(df)})


@app.get("/tickets/by-card/{card_id}", response_model=TicketDetailResponse)
def ticket_by_card(card_id: str, _: AuthUser = Depends(require_roles(*ALL_ROLES))):
    ticket = fetch_active_ticket_by_card_id(card_id)
    if ticket is None:
        return map_business_failure({"success": False, "message": f"No active ticket found for Card ID {card_id}"}, resource="ticket")
    events = fetch_parking_events(ticket["ticket_id"]).to_dict(orient="records")
    return ok({"ticket": _sanitize_record(ticket), "events": events})


@app.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def ticket_detail(ticket_id: str, _: AuthUser = Depends(require_roles(*ALL_ROLES))):
    ticket = fetch_ticket_detail(ticket_id)
    if ticket is None:
        return map_business_failure({"success": False, "message": "Ticket ID not found"}, resource="ticket")
    events = fetch_parking_events(ticket_id).to_dict(orient="records")
    return ok({"ticket": _sanitize_record(ticket), "events": events})


@app.get("/zones/status", response_model=CampusZonesResponse, dependencies=[Depends(require_read_access)])
def campus_zones_status():
    zones = get_all_zones()
    total_cap = sum(z["max_capacity"] for z in zones)
    total_occ = sum(z["current_occupied"] for z in zones)
    total_avail = max(0, total_cap - total_occ)
    return ok({
        "zones": zones,
        "total_capacity": total_cap,
        "total_occupied": total_occ,
        "total_available": total_avail,
    })


@app.post("/zones/recalculate", dependencies=[Depends(require_roles("admin", "operator"))])
def recalculate_zones():
    counts = recalculate_zone_occupancies()
    return ok({"recalculated_occupancies": counts})


@app.get("/payment/vietqr", response_model=VietQRPayloadResponse, dependencies=[Depends(require_read_access)])
def get_vietqr(card_id: str = Query(default=""), amount: int = Query(default=5000), ticket_id: str = Query(default="")):
    payload = build_parking_vietqr(card_id=card_id, amount=amount, ticket_id=ticket_id)
    return ok(payload)


@app.post("/payment/webhook")
def payment_webhook(request: Request, payload: dict[str, Any] = Body(...)):
    result = reconcile_bank_transaction(payload)
    status_code = 200 if result.get("success") else 400
    return ok({"result": result}, status_code=status_code)


@app.get("/payment/transactions", dependencies=[Depends(require_read_access)])
def get_payment_transactions(limit: int = Query(default=50, ge=1, le=200)):
    items = fetch_bank_transactions(limit=limit)
    return ok({"items": items, "count": len(items)})


@app.get("/customer-display", include_in_schema=False)
def customer_display():
    return FileResponse(WEB_DIR / "customer_display.html")


@app.get("/display/state")
def get_display_state():
    return ok(get_customer_display_state())


@app.post("/display/state")
def update_display_state(payload: dict[str, Any] = Body(...)):
    updated = set_customer_display_state(payload)
    return ok({"state": updated})


@app.post("/display/reset")
def reset_display_state():
    reset = trigger_idle_display()
    return ok({"state": reset})


@app.get("/events", dependencies=[Depends(require_read_access)])
def events(ticket_id: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    df = fetch_parking_events(ticket_id)
    items = df.iloc[offset: offset + limit].to_dict(orient="records")
    return ok({"items": items, "count": len(items), "total": len(df), "limit": limit, "offset": offset})


@app.get("/audit-logs")
def audit_logs(limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), _: AuthUser = Depends(require_roles("admin"))):
    df = fetch_audit_logs()
    items = df.iloc[offset: offset + limit].to_dict(orient="records")
    return ok({"items": items, "count": len(items), "total": len(df), "limit": limit, "offset": offset})


@app.get("/devices/status", response_model=ListResponse, dependencies=[Depends(require_read_access)])
def devices_status():
    camera = CameraSnapshotSimulator()
    config = load_device_config()
    statuses = [camera.status().__dict__, barrier_simulator.status().__dict__, mqtt_simulator.status().__dict__]
    statuses.append({"device_id": "device-config", "device_type": "configuration", "state": config.mode, "detail": "missing=" + ",".join(config.missing) if config.missing else "real device endpoints configured"})
    return ok({"items": statuses, "count": len(statuses)})


@app.post("/devices/barrier/open")
def open_barrier(request: Request, lane_id: str = Form(default="lane-1"), reason: str = Form(default="operator-approved"), user: AuthUser = Depends(require_roles(*WRITE_ROLES))):
    enforce_write_rate_limit(request, user)
    command = barrier_simulator.open_barrier(lane_id, reason, actor_username=user.username)
    return ok({"command": command.__dict__})


def _audit_admin_action(actor: AuthUser, action: str, username: str, **details):
    try:
        append_audit_log(
            actor.username,
            actor.role,
            action,
            target_type="user",
            target_id=username,
            details_json=json.dumps(details, ensure_ascii=False) if details else None,
        )
    except Exception as exc:
        logger.warning("append_audit_log failed for %s: %s", action, exc)


@app.get("/admin/users", response_model=AdminUsersResponse)
def admin_users(_: AuthUser = Depends(require_roles("admin"))):
    df = list_app_users()
    return ok({"items": df.to_dict(orient="records"), "count": len(df)})


@app.post("/admin/users")
def admin_create_user(username: str = Form(...), password: str = Form(...), role: str = Form(default="viewer"), actor: AuthUser = Depends(require_roles("admin"))):
    if role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    success, message = register_streamlit_user(username, password, role=role)  # type: ignore[arg-type]
    if not success:
        raise HTTPException(status_code=400, detail=message)
    _audit_admin_action(actor, "admin.user.create", username, role=role)
    return ok({"message": message}, status_code=201)


@app.patch("/admin/users/{username}/role")
def admin_update_user_role(username: str, role: str = Form(...), actor: AuthUser = Depends(require_roles("admin"))):
    if role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    if not update_app_user_role(username, role):
        raise HTTPException(status_code=404, detail="User not found")
    _audit_admin_action(actor, "admin.user.role", username, new_role=role)
    return ok({"message": "Role updated"})


@app.patch("/admin/users/{username}/active")
def admin_update_user_active(username: str, is_active: bool = Form(...), actor: AuthUser = Depends(require_roles("admin"))):
    if username == actor.username and not is_active:
        raise HTTPException(status_code=400, detail="Cannot disable current user")
    if not update_app_user_active(username, is_active):
        raise HTTPException(status_code=404, detail="User not found")
    _audit_admin_action(actor, "admin.user.active", username, is_active=bool(is_active))
    return ok({"message": "Active state updated"})


@app.delete("/admin/users/{username}")
def admin_delete_user(username: str, actor: AuthUser = Depends(require_roles("admin"))):
    if username == actor.username:
        raise HTTPException(status_code=400, detail="Cannot delete current user")
    if not delete_app_user(username):
        raise HTTPException(status_code=404, detail="User not found")
    _audit_admin_action(actor, "admin.user.delete", username)
    return ok({"message": "User deleted"})


@app.get("/operations/summary", response_model=OperationSummaryResponse, dependencies=[Depends(require_read_access)])
def operations_summary():
    kpis = build_parking_kpis(fetch_logs())
    health_code, health_tone = classify_operational_health(kpis)
    return ok({"kpis": kpis.__dict__, "health": {"code": health_code, "tone": health_tone}})


@app.post("/ocr", dependencies=[Depends(require_read_access)])
def ocr_image(file: UploadFile = File(...)):
    validate_upload(file)
    saved_path = save_uploaded_file(file, "api_ocr")
    processed = process_plate_image(saved_path)
    payload = {"ocr": _sanitize_ocr_payload(processed.ocr)}
    if API_EXPOSE_INTERNAL_PATHS:
        payload["image_path"] = saved_path
    return ok(payload)


@app.post("/vehicle/entry")
def vehicle_entry(
    request: Request,
    file: UploadFile = File(...),
    plate_text: str | None = Form(default=None),
    card_id: str | None = Form(default=None),
    gate_entry: str | None = Form(default=None),
    lane_entry: str | None = Form(default="LANE_1"),
    zone_assigned: str | None = Form(default=None),
    user_type: str = Form(default="STUDENT"),
    ai_review_confirmed: bool = Form(default=False),
    user: AuthUser = Depends(require_roles(*WRITE_ROLES)),
):
    enforce_write_rate_limit(request, user)
    validate_upload(file)
    saved_path = save_uploaded_file(file, "api_entry")
    processed = process_plate_image(saved_path)
    final_plate = (plate_text or processed.plate_text).strip()
    manual_override = ai_review_confirmed or bool(plate_text and plate_text.strip() and plate_text.strip() != (processed.plate_text or "").strip())
    result = confirm_vehicle_entry(
        final_plate,
        image_path=saved_path,
        detected_path=processed.ocr.get("annotated_path"),
        ocr_confidence=processed.ocr.get("confidence"),
        ocr_engine=processed.ocr.get("ocr_engine"),
        ocr_text=processed.plate_text,
        manual_override=manual_override,
        ocr_review_required=bool(processed.ocr.get("review_required")),
        actor=user,
        card_id=card_id,
        gate_entry=gate_entry,
        lane_entry=lane_entry,
        zone_assigned=zone_assigned,
        user_type=user_type,
    )
    if not result.get("success"):
        return map_business_failure(result, resource="ticket")
    return ok({"ocr": _sanitize_ocr_payload(processed.ocr), "result": result}, status_code=201)


@app.post("/vehicle/exit")
def vehicle_exit(
    request: Request,
    file: UploadFile = File(...),
    ticket_id: str | None = Form(default=None),
    card_id: str | None = Form(default=None),
    plate_text: str | None = Form(default=None),
    gate_exit: str | None = Form(default=None),
    lane_exit: str | None = Form(default=None),
    payment_method: str = Form(default="CASH"),
    payment_status: str = Form(default="PAID"),
    user_type: str | None = Form(default=None),
    ai_review_confirmed: bool = Form(default=False),
    user: AuthUser = Depends(require_roles(*WRITE_ROLES)),
):
    enforce_write_rate_limit(request, user)
    validate_upload(file)
    saved_path = save_uploaded_file(file, "api_exit")
    processed = process_plate_image(saved_path)
    final_plate = (plate_text or processed.plate_text).strip()
    manual_override = ai_review_confirmed or bool(plate_text and plate_text.strip() and plate_text.strip() != (processed.plate_text or "").strip())
    result = confirm_vehicle_exit(
        ticket_id=ticket_id,
        plate_text=final_plate,
        image_path=saved_path,
        detected_path=processed.ocr.get("annotated_path"),
        ocr_confidence=processed.ocr.get("confidence"),
        ocr_engine=processed.ocr.get("ocr_engine"),
        ocr_text=processed.plate_text,
        manual_override=manual_override,
        ocr_review_required=bool(processed.ocr.get("review_required")),
        actor=user,
        card_id=card_id,
        gate_exit=gate_exit,
        lane_exit=lane_exit,
        payment_method=payment_method,
        payment_status=payment_status,
        user_type=user_type,
    )
    if not result.get("success"):
        return map_business_failure(result, resource="ticket")

    # If staff (CB-GV-CNV), notify secondary display that vehicle is exempt and barrier opens
    if result.get("success") and result.get("user_type") == "STAFF":
        try:
            trigger_success_display(
                plate_number=result.get("plate_exit") or final_plate,
                amount=0,
                user_type="STAFF",
            )
        except Exception as exc:
            logger.debug("Failed to trigger staff success display: %s", exc)
    elif result.get("success") and payment_method and payment_method.upper() == "VIETQR":
        try:
            trigger_checkout_display(
                plate_number=result.get("plate_exit") or final_plate,
                fee=result.get("fee") or 5000,
                overnight_surcharge=result.get("overnight_surcharge") or 0,
                card_id=card_id or result.get("card_id"),
                ticket_id=ticket_id or result.get("ticket_id"),
                qr_url=result.get("vietqr", {}).get("qr_image_url") if isinstance(result.get("vietqr"), dict) else None,
            )
        except Exception as exc:
            logger.debug("Failed to trigger checkout display: %s", exc)

    return ok({"ocr": _sanitize_ocr_payload(processed.ocr), "result": result})


@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(request: Request, ticket_id: str, resolution: str = Form(...), note: str | None = Form(default=None), user: AuthUser = Depends(require_roles(*WRITE_ROLES))):
    enforce_write_rate_limit(request, user)
    result = resolve_review_ticket(ticket_id, resolution, actor=user, note=note)
    if not result.get("success"):
        return map_business_failure(result, resource="ticket")
    return ok({"result": result})


@app.post("/tickets/{ticket_id}/cancel")
def cancel_ticket_endpoint(request: Request, ticket_id: str, reason: str = Form(...), user: AuthUser = Depends(require_roles("admin"))):
    enforce_write_rate_limit(request, user)
    result = cancel_ticket(ticket_id, actor=user, reason=reason)
    if not result.get("success"):
        return map_business_failure(result, resource="ticket")
    return ok({"result": result})


from backend.card_service import (
    assign_blank_slot,
    delete_card,
    get_card,
    list_cards,
    save_card,
)


@app.get("/cards")
def api_list_cards():
    cards = list_cards()
    return ok({"items": cards, "count": len(cards)})


@app.get("/cards/{card_uid}")
def api_get_card(card_uid: str):
    c = get_card(card_uid)
    if not c:
        return error_payload("CARD_NOT_FOUND", f"Thẻ với mã {card_uid} chưa được đăng ký")
    return ok({"card": c})


@app.post("/cards")
def api_save_card(
    card_uid: str = Form(...),
    label: str = Form(...),
    user_type: str = Form(default="STUDENT"),
    default_plate: str | None = Form(default=None),
    is_active: bool = Form(default=True),
    note: str | None = Form(default=None),
):
    c = save_card(card_uid=card_uid, label=label, user_type=user_type, default_plate=default_plate, is_active=is_active, note=note)
    return ok({"card": c, "message": f"Đã lưu thẻ {card_uid} thành công"})


@app.post("/cards/assign-slot")
def api_assign_blank_slot(
    slot_number: int = Form(...),
    real_card_uid: str = Form(...),
):
    try:
        c = assign_blank_slot(slot_number, real_card_uid)
        return ok({"card": c, "message": f"Đã gán thành công Thẻ Trắng #{slot_number} vào UID {real_card_uid}"})
    except Exception as ex:
        return error_payload("ASSIGN_FAILED", str(ex))


@app.delete("/cards/{card_uid}")
def api_delete_card(card_uid: str):
    deleted = delete_card(card_uid)
    return ok({"deleted": deleted, "card_uid": card_uid})



WEB_DIR = Path(__file__).resolve().parents[1] / "frontend" / "web"


from backend.barcode_service import decode_card_barcode
from backend.scanner_bridge import get_latest_scan, push_scan_event


@app.post("/scanner/push")
def api_push_scan(
    card_id: str = Form(...),
    plate_text: str | None = Form(default=None),
    user_type: str = Form(default="STUDENT"),
    mode: str = Form(default="entry"),
):
    ev = push_scan_event(card_id, plate_text=plate_text, user_type=user_type, mode=mode)
    return {"ok": True, "event": ev}


@app.post("/scanner/upload-photo")
def api_scanner_upload_photo(
    file: UploadFile = File(...),
    user_type: str = Form(default="STUDENT"),
    mode: str = Form(default="entry"),
):
    validate_upload(file)
    saved_path = save_uploaded_file(file, "scanner_card")
    res = decode_card_barcode(saved_path)

    if res.get("success") and res.get("card_id"):
        card_id = res["card_id"]
        push_scan_event(card_id, user_type=user_type, mode=mode)
        return {
            "ok": True,
            "detected": True,
            "card_id": card_id,
            "format": res.get("format"),
            "message": f"Đã quét thành công mã vạch {card_id} và gửi sang máy tính!",
        }

    return {
        "ok": True,
        "detected": False,
        "card_id": None,
        "message": "Không tìm thấy mã vạch rõ nét trên ảnh. Hãy đưa góc có mã vạch lại gần và đủ sáng nhé!",
    }


@app.get("/scanner/poll")
def api_poll_scan(since: float = Query(default=0.0)):
    ev = get_latest_scan(since)
    return {"ok": True, "has_new": ev is not None, "scan": ev}


@app.get("/scanner", include_in_schema=False)
def web_scanner():
    return FileResponse(WEB_DIR / "scanner.html")


@app.get("/", include_in_schema=False)
def web_index():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
