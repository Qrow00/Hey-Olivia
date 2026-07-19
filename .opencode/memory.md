# Project Memory

## Project: J.A.R.V.I.S.
- **Path:** `C:\Users\toshi\Documents\main jarvis`
- **Description:** Personal AI Assistant
- **Type:** TypeScript/Node.js (ESM) + FastAPI (Python) + Flutter (Dart)

## Obsidian Vault
- **Location:** `C:\Users\toshi\Documents\main jarvis\vault`
- **Created:** 2026-07-18

## Roadmap
- **Location:** `vault/ROADMAP.md`
- **Timeline:** 1-2 months MVP
- **Platform:** Flutter (Android, Windows, Linux)
- **Backend:** FastAPI (Python) on HP EliteDesk
- **Current Phase:** Phase 6 — Future Proofing ✅ COMPLETE
- **Completed:** Phases 1-6 ✅ (Foundation, Core Voice, Device Management, Screen Sharing, Smart Home & Polish, AI Vision, Future Proofing)

## Project Structure
- `.obsidian/` — Original Obsidian config (root level)
- `vault/` — Separate Obsidian vault for documentation/notes
- `types/` — TypeScript type definitions (all 10 data structures complete)
- `backend/` — FastAPI (Python) server
  - `app/main.py` — FastAPI app entry
  - `app/models/` — SQLAlchemy models
  - `app/routers/` — REST + WebSocket endpoints
    - `devices.py`, `conversations.py`, `settings.py`, `commands.py`
    - `voice.py`, `screen_share.py`, `websocket.py`
    - `cameras.py` — RTSP camera management
    - `wearables.py` — Wearable health data
    - `smart_home.py` — IoT device control
  - `app/services/` — Business logic
    - `voice_service.py` — STT/TTS/LLM pipeline
    - `screen_share_service.py` — Screen capture
    - `rtsp_service.py` — RTSP camera streaming
    - `wearable_service.py` — Health monitoring
    - `smart_home_service.py` — MQTT/HTTP device control
    - `command_registry.py` — Voice command parsing
  - `requirements.txt` — Python dependencies
- `client/` — Flutter app (Android, Windows, Linux)
  - `lib/main.dart` — App entry with bottom nav (7 tabs)
  - `lib/screens/` — UI screens
    - `home_screen.dart`, `devices_screen.dart`, `screen_share_screen.dart`
    - `camera_screen.dart` — Camera viewer
    - `wearable_screen.dart` — Health dashboard
    - `smart_home_screen.dart` — Device control grid
    - `settings_screen.dart` — Full configuration
  - `lib/services/` — API and WebSocket services
    - `websocket_service.dart`, `voice_service.dart`, `device_service.dart`
    - `screen_share_service.dart`, `camera_service.dart`
    - `wearable_service.dart`, `smart_home_service.dart`
    - `notification_service.dart` — Alert system
  - `lib/models/` — Data models
    - `device.dart`, `conversation.dart`, `wearable.dart`, `smart_device.dart`
  - `lib/widgets/` — Reusable components
    - `avatar_widget.dart` (5-state animated), `device_card.dart`
  - `client/android/` — Native Kotlin (ScreenCaptureService)
- `run-backend.ps1` — Start backend server
- `run-client.ps1` — Start Flutter client
- `DATA_STRUCTURE.md` — Data structure documentation (15 schemas)

## Run Commands
- Backend: `.\run-backend.ps1` or `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Client: `.\run-client.ps1` or `flutter run -d windows`
- Flutter path: `C:\flutter\bin` (add to PATH)

## Recent Changes
- 2026-07-19: Phase 6 Complete — Future Proofing
  - Plugin system: abstract DevicePlugin base, PluginManager, motion detector plugin
  - API versioning: all endpoints moved to /api/v1/ prefix
  - Documentation: SETUP.md, API_DOCS.md with full endpoint reference
  - Testing: 17 tests passing (API routes, command registry, plugins)
  - Installed missing deps: opencv-python, paho-mqtt, pytest, pytest-asyncio
- 2026-07-19: Phase 5.6 Complete — AI Vision System
  - Vision service with llava:7b integration for camera analysis
  - Proactive observation modes (watch, scan, alert)
  - 10+ vision voice commands (what do you see, watch camera, scan, who's there)
  - Flutter AI Vision dashboard with real-time analysis display
  - Motion detection, people counting, activity recognition
  - Security alerts for suspicious activity detection
- 2026-07-19: Phase 5 Complete — Smart Home & Polish
  - RTSP camera integration with live streaming and viewer management
  - Wearable device support (heart rate, SpO2, sleep, steps, calories, stress, temperature)
  - Smart home control (MQTT, HTTP, Tasmota, Shelly protocols)
  - Voice command registry with regex pattern matching
  - Enhanced settings screen with all configuration options
  - Notification service for alerts and events
- 2026-07-19: Phase 2-4 Complete — Core Voice, Device Management, Screen Sharing
  - Whisper STT, Edge-TTS, Ollama LLM integration
  - Full CRUD device API with heartbeat and capabilities
  - WebSocket screen sharing with Android MediaProjection
- 2026-07-18: Phase 1 Complete — Backend (FastAPI) + Client (Flutter) initialized

## Git
- **Remote:** https://github.com/Qrow00/Hey-Olivia.git
- **Branch:** main
- **Last commit:** Phase 2-4: Core Voice, Device Management, Screen Sharing

## Session Log
- **2026-07-18:** First session
  - Completed Phase 1 (Foundation)
  - Backend running on port 8000
  - Flutter client builds clean
  - Pushed to GitHub
- **2026-07-19:** Second session
  - Completed Phases 2-4 (Voice, Devices, Screen Share)
  - Whisper, Edge-TTS, Ollama integration
  - Native Kotlin screen capture
- **2026-07-19:** Third session
  - Completed Phase 5 (Smart Home & Polish)
  - RTSP, Wearables, Smart Home, Commands, Settings
- **2026-07-19:** Fourth session
  - Completed Phase 5.6 (AI Vision)
  - JARVIS can now see through CCTV cameras
  - llava:7b vision model integration
  - Proactive observation and security alerts
- **2026-07-19:** Fifth session
  - Completed Phase 6 (Future Proofing)
  - Plugin system with motion detector plugin
  - API versioning (/api/v1/)
  - Full documentation (SETUP.md, API_DOCS.md)
  - 17 tests passing
  - **All MVP phases complete**
