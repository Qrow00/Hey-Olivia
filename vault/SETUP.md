# J.A.R.V.I.S. Setup Guide

## Requirements

### Backend (HP EliteDesk)
- Python 3.10+
- 8GB+ RAM (for Whisper + Ollama)
- 20GB+ free disk space
- Network: Tailscale or local network

### Client
- Flutter SDK 3.12+
- Android Studio (for Android)
- Visual Studio (for Windows)

---

## Backend Setup

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Ollama

```bash
# Windows
winget install Ollama.Ollama

# Pull models
ollama pull llama3.2
ollama pull llava:7b  # For vision
```

### 3. Start Backend

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Configure Tailscale (Optional)

For remote access:
```bash
tailscale up
# Note your Tailscale IP (e.g., 100.x.x.x)
```

---

## Client Setup

### 1. Install Flutter

```bash
# Download Flutter SDK
# Add to PATH: C:\flutter\bin

# Verify
flutter doctor
```

### 2. Configure Server URL

Edit `client/lib/main.dart`:
```dart
_webSocketService.connect('ws://YOUR_SERVER_IP:8000/ws');
```

### 3. Run Client

```bash
cd client

# Android
flutter run -d android

# Windows
flutter run -d windows
```

---

## Configuration

### Smart Home (MQTT)

1. Install MQTT broker:
```bash
# Docker
docker run -d -p 1883:1883 eclipse-mosquitto

# Or install Mosquitto
```

2. Connect via app settings or API:
```bash
curl -X POST http://localhost:8000/api/v1/smart-home/mqtt/connect \
  -H "Content-Type: application/json" \
  -d '{"broker": "localhost", "port": 1883}'
```

### Cameras (RTSP)

Add cameras via API:
```bash
curl -X POST http://localhost:8000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Front Door",
    "url": "rtsp://192.168.1.100:554/stream",
    "username": "admin",
    "password": "password",
    "type": "cctv",
    "location": "Front Door"
  }'
```

### Wearables

Register a wearable:
```bash
curl -X POST http://localhost:8000/api/v1/wearables \
  -H "Content-Type: application/json" \
  -d '{"name": "My Watch", "type": "smartwatch", "platform": "android"}'
```

Record health data:
```bash
curl -X POST http://localhost:8000/api/v1/wearables/DEVICE_ID/health \
  -H "Content-Type: application/json" \
  -d '{"metric": "heart_rate", "value": 72, "unit": "bpm"}'
```

---

## Voice Commands

JARVIS supports these voice commands out of the box:

| Command | Action |
|---------|--------|
| "What time is it?" | Tells current time |
| "Turn on the lights" | Turns on smart lights |
| "Turn off the AC" | Turns off air conditioning |
| "Show me the cameras" | Shows camera feeds |
| "What do you see?" | AI analyzes camera view |
| "Watch the front door" | Starts monitoring camera |
| "What's my heart rate?" | Reads wearable heart rate |
| "Scan cameras" | Scans all cameras for activity |
| "Share my screen" | Starts screen sharing |
| "Play some music" | Plays music |

---

## Troubleshooting

### Backend won't start
- Check Python version: `python --version`
- Check port 8000: `netstat -ano | findstr :8000`
- Check Ollama: `ollama list`

### Client won't connect
- Verify server URL in `main.dart`
- Check Tailscale connection
- Check firewall settings

### Voice not working
- Verify Whisper model downloaded
- Check microphone permissions
- Test Ollama: `ollama run llama3.2`

### Vision not working
- Pull llava model: `ollama pull llava:7b`
- Check camera RTSP URL
- Verify camera is online: `curl http://localhost:8000/api/v1/cameras`

---

## Related

- [[AGENTS]] — project rules
- [[ROADMAP]] — project timeline
- [[DATA_STRUCTURE]] — data models
- [[API_DOCS]] — API reference
- [[JARVIS_ENHANCEMENT_PLAN]] — future features
- [[Memory Map]] — vault index
