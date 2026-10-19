from integrations.barrier_service import BarrierSimulator
from integrations.camera_service import CameraSnapshotSimulator
from integrations.mqtt_adapter import MqttAdapterSimulator


def test_device_simulators_produce_status_and_commands(tmp_path):
    image_path = tmp_path / "plate.jpg"
    image_path.write_bytes(b"fake")

    camera = CameraSnapshotSimulator("lane-test")
    event = camera.ingest_uploaded_snapshot(str(image_path), plate_text="66-B1 123.45", confidence=0.88)
    assert event.lane_id == "lane-test"
    assert camera.status().state == "SIMULATED"

    barrier = BarrierSimulator()
    command = barrier.open_barrier("lane-test", "unit-test", actor_username="operator")
    assert command.action == "OPEN"
    assert barrier.status().state == "SIMULATED"

    mqtt = MqttAdapterSimulator()
    assert mqtt.publish_sensor_event("its/parking/events", event) is True
    assert mqtt.status().state == "SIMULATED"
