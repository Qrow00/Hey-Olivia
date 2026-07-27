# Smart Home Integration

## Protocols
- **MQTT** — primary protocol (Tasmota, Shelly devices)
- **HTTP** — REST API fallback
- **Hue** — Philips Hue bridge support

## Device Types
- Lights, switches, thermostats, locks
- Fans, curtains, sensors, plugs
- Speakers, cameras

## MQTT Setup

### Broker
```bash
docker run -d -p 1883:1883 eclipse-mosquitto
```

### Connect
```bash
curl -X POST http://localhost:8000/api/v1/smart-home/mqtt/connect \
  -H "Content-Type: application/json" \
  -d '{"broker": "localhost", "port": 1883}'
```

## Control Endpoints
- `/api/v1/smart-home/{id}/on` — turn on
- `/api/v1/smart-home/{id}/off` — turn off
- `/api/v1/smart-home/{id}/toggle` — toggle
- `/api/v1/smart-home/{id}/brightness` — set brightness
- `/api/v1/smart-home/{id}/color` — set color

## Voice Commands
- "Turn on the lights"
- "Turn off the AC"
- "Set brightness to 50%"
- "Lock the door"

## Related

- [[DATA_STRUCTURE]] — SmartDevice schema
- [[API_DOCS]] — smart home endpoints
- [[JARVIS_ENHANCEMENT_PLAN]] — Phase 4 routines
- [[Memory Map]] — vault index
