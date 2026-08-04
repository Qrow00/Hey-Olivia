# Jarvis AI Assistant — Project Rules

## Architecture

- **Backend:** Python 3.11+ / FastAPI + SQLite (async via aiosqlite)
- **Client:** Flutter (Dart) — voice-first UI
- **AI:** Ollama (local LLMs) + Whisper (local STT)
- **Voice:** edge-tts (TTS), Chatterbox TTS (Phase 8 — voice cloning)
- **Smart Home:** MQTT + Tasmota devices
- **Browser:** Playwright (hermes_browser.py)
- **Target hardware:** NVIDIA GTX 1050 (Pascal, CC 6.1, 4GB VRAM) — Ollama LLM on GPU (since v0.12.0), Whisper STT on CUDA

## Backend Structure

```
backend/
  app/
    models/        # SQLAlchemy ORM models (device, conversation, wearable, smart_device, etc.)
    plugins/       # Plugin system (DevicePlugin base, PluginManager)
    routers/       # FastAPI route handlers (devices, voice, commands, cameras, wearables, smart_home, screen_share, websocket, settings, conversations)
    services/      # Business logic (22 services — see Key Files below)
  requirements.txt
```

## Flutter Structure

```
client/
  lib/
    main.dart       # App entry with bottom navigation
    screens/        # home, devices, screen_share, camera, wearable, smart_home, settings, monitoring, personality
    services/       # API + WebSocket clients for each backend service
    models/         # device, conversation, wearable, smart_device
    widgets/        # avatar_widget (5-state), device_card, etc.
```

## Key Files

- `backend/app/services/voice_service.py` — TTS/STT (edge-tts, Whisper)
- `backend/app/services/hermes_browser.py` — Playwright browser automation
- `backend/app/services/mqtt_service.py` — Smart home MQTT
- `backend/app/services/monitoring_service.py` — System monitoring (CPU/RAM/disk/GPU)
- `backend/app/services/alert_engine.py` — Threshold-based alerting
- `backend/app/services/activity_logger.py` — Process/window/file change logging
- `backend/app/services/briefing_service.py` — Morning briefing orchestrator
- `backend/app/services/weather_service.py` — Open-Meteo weather
- `backend/app/services/news_service.py` — RSS news headlines
- `backend/app/services/email_service.py` — Gmail integration
- `backend/app/services/routine_service.py` — Multi-step automation routines
- `backend/app/services/wake_word_service.py` — openWakeWord detection
- `backend/app/services/suggestion_engine.py` — Proactive suggestions
- `backend/app/services/personality_enhancer.py` — Jarvis wit/flair
- `backend/app/services/device_mesh_service.py` — Cross-device orchestration
- `backend/app/services/screen_context_service.py` — OCR screen analysis
- `backend/app/services/notification_service.py` — System notifications
- `backend/app/services/command_registry.py` — Voice command parsing
- `backend/app/services/conversation_memory.py` — Conversation history
- `backend/app/services/knowledge_service.py` — User knowledge base
- `backend/app/services/voice_profile_service.py` — Switchable TTS voices
- `backend/app/services/personality_service.py` — Personality configuration

## Code Conventions

- Python: type hints, async/await, Pydantic models
- No comments unless requested
- Follow existing patterns in each file
- Use `httpx` for HTTP clients, `asyncio` for concurrency
- Security: never log secrets, never commit API keys

## Local Models

- `qwen2.5-coder:7b` — coding tasks (Ollama)
- `llama3.2:latest` — general conversation (Ollama)
- `whisper` — speech-to-text (local, CPU)

## Related

- [[ROADMAP]] — project timeline and phases
- [[DATA_STRUCTURE]] — data models and schemas
- [[SETUP]] — installation and configuration
- [[API_DOCS]] — backend API reference
- [[JARVIS_ENHANCEMENT_PLAN]] — future feature roadmap
- [[Memory Map]] — vault index
