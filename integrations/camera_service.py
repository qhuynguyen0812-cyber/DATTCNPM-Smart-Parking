from pathlib import Path
from uuid import uuid4

from integrations.events import DeviceStatus, SensorEvent


class CameraSnapshotSimulator:
    def __init__(self, lane_id: str = "lane-1"):
        self.lane_id = lane_id

    def ingest_uploaded_snapshot(self, image_path: str, plate_text: str | None = None, confidence: float | None = None) -> SensorEvent:
        return SensorEvent(
            event_id=f"sensor-{uuid4().hex[:12]}",
            source="upload",
            lane_id=self.lane_id,
            image_path=str(Path(image_path)),
            plate_text=plate_text,
            confidence=confidence,
        )

    def status(self) -> DeviceStatus:
        return DeviceStatus(device_id=f"camera-{self.lane_id}", device_type="camera", state="SIMULATED", detail="Upload/snapshot simulator active")
