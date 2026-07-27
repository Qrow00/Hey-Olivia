# Jarvis AI Assistant — Project Rules

## Architecture

- **Backend:** Python 3.11+ / FastAPI + SQLite (async via aiosqlite)
- **Client:** Flutter (Dart) — voice-first UI
- **AI:** Ollama (local LLMs) + Whisper (local STT)
- **Voice:** edge-tts (TTS), Chatterbox TTS (Phase 8 — voice cloning)
- **Smart Home:** MQTT + Tasmota devices
- **Browser:** Playwright (hermes_browser.py)
- **Target hardware:** HP EliteDesk, AMD RX 6600 (RDNA 2, 8GB VRAM)

## Backend Structure

```
backend/
  app/
    models/        # SQLAlchemy ORM models
    plugins/       # Plugin system
    routers/       # FastAPI route handlers
    services/      # Business logic (voice, browser, MQTT, etc.)
  requirements.txt
```

## Key Files

- `backend/app/services/voice_service.py` — TTS/STT (edge-tts, Whisper)
- `backend/app/services/hermes_browser.py` — Playwright browser automation
- `backend/app/services/mqtt_service.py` — Smart home MQTT

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
