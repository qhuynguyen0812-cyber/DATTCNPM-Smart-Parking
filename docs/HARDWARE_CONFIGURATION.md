# Hardware Configuration Guide

The project supports simulator mode by default and becomes hardware-ready when these environment variables are configured:

```env
ITS_CAMERA_URL=rtsp://user:password@camera-ip:554/stream1
ITS_MQTT_URL=mqtt://user:password@mqtt-host:1883/its
ITS_BARRIER_URL=http://barrier-controller-ip/api/barrier
```

## Current Behavior

- If any value is missing, `production_check.py` reports `hardware_mode` as fail for production.
- If all values are present, `hardware_mode` reports pass.
- Device simulators remain useful for demo/staging without physical hardware.

## Expected Devices

### Camera

Recommended protocols:

- RTSP IP camera stream.
- HTTP snapshot endpoint.

Examples:

```env
ITS_CAMERA_URL=rtsp://admin:password@192.168.1.10:554/stream1
ITS_CAMERA_URL=http://192.168.1.10/snapshot.jpg
```

### MQTT Broker

Used for publishing sensor/device events when a real broker is available.

```env
ITS_MQTT_URL=mqtt://its_user:password@192.168.1.20:1883/its
```

### Barrier Controller

Expected to expose an HTTP endpoint for barrier commands.

```env
ITS_BARRIER_URL=http://192.168.1.30/api/barrier
```

## Production Checklist

1. Fill all three hardware endpoint variables in `.env`.
2. Restart API/Streamlit processes.
3. Run:

```powershell
python scripts\production_check.py
python scripts\cv_doctor.py
```

4. Verify `/devices/status` from the API.
5. Perform one supervised field test for vehicle entry and exit.

## Security Notes

- Do not commit `.env`.
- Use dedicated device credentials, not personal/admin camera passwords.
- Restrict camera/barrier/MQTT devices to the parking system network segment.
- Rotate credentials before real deployment.
