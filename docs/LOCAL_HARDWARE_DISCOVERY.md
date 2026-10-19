# Local Hardware Discovery Report

## Network Context

Local machine:

```text
IPv4: 192.168.1.181
Gateway: 192.168.1.1
Subnet: 192.168.1.0/24
```

ARP cache found:

```text
192.168.1.1    router/gateway
192.168.1.214  LAN device, no common hardware ports confirmed
```

## Local Services

Detected important local listeners:

```text
0.0.0.0:20128      9Router proxy
127.0.0.1:11434    Ollama/local LLM service
0.0.0.0:3306       MySQL
```

9Router endpoint is available at:

```text
http://localhost:20128/v1
```

## Safe LAN Probe Results

Checked common camera/MQTT/barrier ports on:

```text
192.168.1.1
192.168.1.214
```

Open ports found:

```text
192.168.1.1:80
192.168.1.1:443
```

No confirmed camera/MQTT/barrier endpoint found from safe probing.

## Decision

No hardware endpoint was written into `.env` because guessing would create false production readiness.

Current required variables remain:

```env
ITS_CAMERA_URL=
ITS_MQTT_URL=
ITS_BARRIER_URL=
```

## Next Safe Options

1. Open router admin page and identify connected camera/barrier device IPs.
2. Provide device IP/credentials if already known.
3. If you want a broader authorized LAN discovery, run a dedicated network scanner such as Nmap manually and share results.
4. Once endpoints are known, fill:

```env
ITS_CAMERA_URL=rtsp://user:password@device-ip:554/stream1
ITS_MQTT_URL=mqtt://user:password@broker-ip:1883/its
ITS_BARRIER_URL=http://barrier-ip/api/barrier
```

Then run:

```powershell
python scripts\production_check.py
```
