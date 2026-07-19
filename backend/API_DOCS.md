# J.A.R.V.I.S. Backend API

## Quick Start

### Prerequisites
- Python 3.10+
- Ollama (for LLM)
- FFmpeg (for audio processing)

### Installation

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Development
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify

```bash
# Health check
curl http://localhost:8000/

# API info
curl http://localhost:8000/api/v1
```

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### WebSocket
```
ws://localhost:8000/ws
```

---

## Endpoints

### Devices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices` | List all devices |
| POST | `/api/v1/devices` | Register a device |
| GET | `/api/v1/devices/{id}` | Get device details |
| PUT | `/api/v1/devices/{id}` | Update device |
| DELETE | `/api/v1/devices/{id}` | Remove device |

### Cameras (RTSP)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cameras` | List all cameras |
| POST | `/api/v1/cameras` | Add a camera |
| GET | `/api/v1/cameras/{id}` | Get camera details |
| DELETE | `/api/v1/cameras/{id}` | Remove camera |
| POST | `/api/v1/cameras/{id}/stream/start` | Start stream |
| POST | `/api/v1/cameras/{id}/stream/stop` | Stop stream |
| POST | `/api/v1/cameras/{id}/snapshot` | Take snapshot |

### Wearables (Health)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/wearables` | List wearables |
| POST | `/api/v1/wearables` | Register wearable |
| GET | `/api/v1/wearables/{id}` | Get wearable details |
| DELETE | `/api/v1/wearables/{id}` | Remove wearable |
| POST | `/api/v1/wearables/{id}/health` | Record health data |
| GET | `/api/v1/wearables/{id}/health` | Get health summary |
| GET | `/api/v1/wearables/{id}/health/history` | Get health history |

### Smart Home
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/smart-home` | List devices |
| POST | `/api/v1/smart-home` | Add device |
| DELETE | `/api/v1/smart-home/{id}` | Remove device |
| POST | `/api/v1/smart-home/{id}/control` | Control device |
| POST | `/api/v1/smart-home/{id}/on` | Turn on |
| POST | `/api/v1/smart-home/{id}/off` | Turn off |
| POST | `/api/v1/smart-home/{id}/toggle` | Toggle |
| POST | `/api/v1/smart-home/{id}/brightness` | Set brightness |
| POST | `/api/v1/smart-home/{id}/color` | Set color |
| POST | `/api/v1/smart-home/mqtt/connect` | Connect MQTT |

### Vision (AI)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/vision/analyze` | Analyze camera feed |
| POST | `/api/v1/vision/quick-look/{camera_id}` | Quick camera look |
| POST | `/api/v1/vision/scan-all` | Scan all cameras |
| POST | `/api/v1/vision/observe/start` | Start observation |
| POST | `/api/v1/vision/observe/stop/{session_id}` | Stop observation |
| GET | `/api/v1/vision/observe/sessions` | List observation sessions |

### Commands
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/commands` | List all commands |
| POST | `/api/v1/commands/parse` | Parse a command |
| POST | `/api/v1/commands/execute` | Execute a command |

### Plugins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/plugins` | List all plugins |
| GET | `/api/v1/plugins/capabilities` | List capabilities |
| GET | `/api/v1/plugins/{id}` | Get plugin details |
| POST | `/api/v1/plugins/{id}/enable` | Enable plugin |
| POST | `/api/v1/plugins/{id}/disable` | Disable plugin |
| POST | `/api/v1/plugins/command` | Execute plugin command |

### Voice
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/voice/stt` | Speech to text |
| POST | `/api/v1/voice/tts` | Text to speech |
| POST | `/api/v1/voice/chat` | Chat completion |

### Screen Share
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/screen/sessions` | List sessions |
| POST | `/api/v1/screen/analyze` | Analyze screen |

---

## WebSocket Events

### Client → Server
| Event | Description |
|-------|-------------|
| `ping` | Keepalive |
| `voice_chunk` | Send audio for STT |
| `text_message` | Send text message |
| `device_register` | Register device |
| `device_heartbeat` | Device heartbeat |
| `camera_view` | View camera feed |
| `vision_analyze` | Analyze camera |
| `vision_quick_look` | Quick camera look |
| `vision_observe_start` | Start observation |
| `wearable_health_update` | Health data update |

### Server → Client
| Event | Description |
|-------|-------------|
| `pong` | Keepalive response |
| `avatar_state` | Avatar state change |
| `voice_response` | Voice response with audio |
| `text_response` | Text response |
| `command_response` | Command execution result |
| `camera_frame` | Camera frame data |
| `vision_result` | AI vision analysis |
| `vision_observation` | Observation update |
| `vision_alert` | Security alert |
| `wearable_health_data` | Health metric update |

---

## Voice Commands

| Category | Commands |
|----------|----------|
| **System** | "what time", "what date", "remind me to..." |
| **Smart Home** | "turn on/off lights", "set brightness", "lock door" |
| **Camera** | "show cameras", "take photo", "look at camera" |
| **Vision** | "what do you see", "scan cameras", "watch camera" |
| **Health** | "heart rate", "blood oxygen", "steps today" |
| **Screen** | "share screen", "stop screen share" |
| **Media** | "play music", "stop music" |
| **Info** | "weather in...", "search for..." |
