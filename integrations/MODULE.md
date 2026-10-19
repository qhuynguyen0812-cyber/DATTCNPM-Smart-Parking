# Integrations Module

## Responsibility

The `integrations/` module defines external device boundaries for camera, MQTT, and barrier control.

## Current State

Simulator adapters are implemented and production readiness checks require real endpoint configuration before field deployment.

## Files

| File | Purpose |
|---|---|
| `device_config.py` | Loads device endpoint environment variables |
| `camera_service.py` | Camera/upload snapshot simulator |
| `mqtt_adapter.py` | MQTT simulator contract |
| `barrier_service.py` | Barrier simulator contract |
| `events.py` | Device event dataclasses |

## Required Production Variables

```env
ITS_CAMERA_URL=
ITS_MQTT_URL=
ITS_BARRIER_URL=
```

## Rules

- Do not hard-code device credentials.
- Do not fake production readiness with placeholder endpoints.
- Simulator mode is acceptable for demo/staging only.
- Real hardware adapters should preserve the same method contracts as simulators.

## Future Implementation Layers

- `CameraClient` for RTSP/HTTP snapshot capture.
- `MqttPublisher` for real broker publish.
- `BarrierClient` for HTTP controller commands.
- Health/status checks for each adapter.
