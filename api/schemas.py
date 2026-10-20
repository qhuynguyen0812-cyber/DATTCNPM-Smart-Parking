from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel):
    ok: bool = True


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ApiError


class UserIdentity(BaseModel):
    username: str
    role: str


class AuthResponse(ApiResponse):
    access_token: str
    token_type: str = "bearer"
    user: UserIdentity


class ListResponse(ApiResponse):
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class HealthResponse(BaseModel):
    status: str
    schema_version: int


class ReadinessCheck(BaseModel):
    name: str
    status: str
    detail: str


class ReadinessResponse(ApiResponse):
    status: str
    checks: list[ReadinessCheck]


class ScorecardItem(BaseModel):
    criterion: str
    score: float
    status: str
    evidence: str


class ScorecardResponse(ApiResponse):
    overall_score: float
    items: list[ScorecardItem]


class OperationSummaryResponse(ApiResponse):
    kpis: dict[str, Any]
    health: dict[str, str]


class DeviceStatusResponse(ListResponse):
    pass


class ZoneStatusItem(BaseModel):
    zone_id: str
    zone_name: str
    max_capacity: int
    current_occupied: int
    available_slots: int
    is_full: bool
    occupancy_rate: float


class CampusZonesResponse(ApiResponse):
    zones: list[ZoneStatusItem] = Field(default_factory=list)
    total_capacity: int = 0
    total_occupied: int = 0
    total_available: int = 0


class VietQRPayloadResponse(ApiResponse):
    bank_id: str
    account_no: str
    account_name: str
    amount: int
    memo: str
    card_id: str
    ticket_id: str
    qr_image_url: str


class ParkingLogRecord(BaseModel):
    ticket_id: str | None = None
    card_id: str | None = None
    plate_entry: str | None = None
    plate_exit: str | None = None
    entry_time: str | None = None
    exit_time: str | None = None
    status: str | None = None
    match_result: str | None = None
    review_required: int | None = None
    review_reason: str | None = None
    gate_entry: str | None = None
    lane_entry: str | None = None
    zone_assigned: str | None = None
    gate_exit: str | None = None
    lane_exit: str | None = None
    fee: int | None = None
    overnight_surcharge: int | None = None
    payment_method: str | None = None
    payment_status: str | None = None
    paid_at: str | None = None


class ParkingEventRecord(BaseModel):
    id: int | None = None
    ticket_id: str | None = None
    event_type: str | None = None
    actor_username: str | None = None
    actor_role: str | None = None
    plate_text: str | None = None
    confidence: float | None = None
    source: str | None = None
    created_at: str | None = None


class AuditLogRecord(BaseModel):
    id: int | None = None
    actor_username: str | None = None
    actor_role: str | None = None
    action: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    created_at: str | None = None


class TicketDetailResponse(ApiResponse):
    ticket: dict[str, Any]
    events: list[dict[str, Any]] = Field(default_factory=list)


class UserRecord(BaseModel):
    username: str
    role: str
    is_active: int | None = None
    created_at: str | None = None
    failed_login_count: int | None = None
    locked_until: str | None = None
    last_login_at: str | None = None


class AdminUsersResponse(ApiResponse):
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
