from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

EventSource = Literal["camera", "upload", "mqtt", "operator", "simulator"]
BarrierAction = Literal["OPEN", "DENY"]
DeviceState = Literal["ONLINE", "OFFLINE", "SIMULATED"]


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class SensorEvent:
    event_id: str
    source: EventSource
    lane_id: str
    image_path: str | None = None
    plate_text: str | None = None
    confidence: float | None = None
    created_at: str = field(default_factory=lambda: _utcnow_naive().isoformat(timespec="seconds"))


@dataclass(frozen=True)
class BarrierCommand:
    action: BarrierAction
    lane_id: str
    reason: str
    actor_username: str | None = None
    created_at: str = field(default_factory=lambda: _utcnow_naive().isoformat(timespec="seconds"))


@dataclass(frozen=True)
class DeviceStatus:
    device_id: str
    device_type: str
    state: DeviceState
    detail: str
    updated_at: str = field(default_factory=lambda: _utcnow_naive().isoformat(timespec="seconds"))
