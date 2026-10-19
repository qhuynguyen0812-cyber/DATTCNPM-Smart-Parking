from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DeviceConfig:
    camera_url: str
    mqtt_url: str
    barrier_url: str

    @property
    def mode(self) -> str:
        return "READY_FOR_REAL_DEVICE" if self.camera_url and self.mqtt_url and self.barrier_url else "SIMULATED"

    @property
    def missing(self) -> list[str]:
        missing = []
        if not self.camera_url:
            missing.append("ITS_CAMERA_URL")
        if not self.mqtt_url:
            missing.append("ITS_MQTT_URL")
        if not self.barrier_url:
            missing.append("ITS_BARRIER_URL")
        return missing


def load_device_config() -> DeviceConfig:
    return DeviceConfig(
        camera_url=os.getenv("ITS_CAMERA_URL", ""),
        mqtt_url=os.getenv("ITS_MQTT_URL", ""),
        barrier_url=os.getenv("ITS_BARRIER_URL", ""),
    )
