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

## gstack Workflow

Available skills (use `/skill-name` to activate):

**Planning:**
- `/office-hours` — product interrogation, reframing
- `/plan-ceo-review` — scope challenge, 10-star product thinking
- `/plan-eng-review` — architecture, data flow, test plans
- `/autoplan` — runs CEO → design → eng review automatically

**Build:**
- `/review` — staff engineer bug hunt, auto-fix
- `/investigate` — root-cause debugging
- `/qa` — browser-based QA testing

**Ship:**
- `/ship` — tests, coverage, push, open PR
- `/retro` — weekly retrospective

**Safety:**
- `/careful` — warns before destructive commands
- `/freeze` — lock edits to one directory
- `/guard` — full safety mode

## Available Commands

- `/common-ground` — validate project assumptions
- `/discovery/create` — create discovery document
- `/planning/epic-plan` — epic planning
- `/execution/execute-ticket` — execute a ticket
- `/retrospectives/complete-sprint` — sprint retro

## Model Rules

- Use `ollama/qwen2.5-coder:7b` for code generation and review
- Use `ollama/llama3.2:latest` for conversation and planning
- Always verify local model availability before assuming GPU access
- RX 6600 = RDNA 2, no CUDA, limited ROCm on Windows
