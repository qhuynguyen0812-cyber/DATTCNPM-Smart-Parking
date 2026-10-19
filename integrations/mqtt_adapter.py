from integrations.events import DeviceStatus, SensorEvent


class MqttAdapterSimulator:
    def __init__(self):
        self.published: list[SensorEvent] = []

    def publish_sensor_event(self, topic: str, event: SensorEvent) -> bool:
        self.published.append(event)
        return True

    def status(self) -> DeviceStatus:
        return DeviceStatus(device_id="mqtt-simulator", device_type="mqtt", state="SIMULATED", detail=f"{len(self.published)} events published")


mqtt_simulator = MqttAdapterSimulator()
