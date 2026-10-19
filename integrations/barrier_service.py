from integrations.events import BarrierCommand, DeviceStatus


class BarrierSimulator:
    def __init__(self):
        self.commands: list[BarrierCommand] = []

    def open_barrier(self, lane_id: str, reason: str, actor_username: str | None = None) -> BarrierCommand:
        command = BarrierCommand(action="OPEN", lane_id=lane_id, reason=reason, actor_username=actor_username)
        self.commands.append(command)
        return command

    def deny_barrier(self, lane_id: str, reason: str, actor_username: str | None = None) -> BarrierCommand:
        command = BarrierCommand(action="DENY", lane_id=lane_id, reason=reason, actor_username=actor_username)
        self.commands.append(command)
        return command

    def status(self) -> DeviceStatus:
        return DeviceStatus(device_id="barrier-simulator", device_type="barrier", state="SIMULATED", detail=f"{len(self.commands)} commands issued")


barrier_simulator = BarrierSimulator()
