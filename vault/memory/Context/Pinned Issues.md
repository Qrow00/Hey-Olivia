---
title: Pinned Issues — Current Session (Jul 29)
date: 2026-07-29
tags: [context, issues, debugging, llm]
type: context
status: permanent
related: [[AGENTS]], [[MASTER_PLAN]], [[Memory Map]]
---

## Backend Crashes

### Port conflict (Errno 10048)
Old python process holds port 8000 after shell dies. Fix: `Stop-Process -Name python` before restart.
In `run-backend.ps1`: Ollama + lifecycle management implemented.

## LLM Selection

### 1. Settings PATCH 307 Redirect — FIXED
**File:** `backend/app/routers/settings.py`
Changed all routes from `"/"` to `""` so FastAPI doesn't 307-redirect PATCH to `/api/v1/settings/`.
Flutter `http` package doesn't follow 307 for PATCH/verbs.

### 2. Voice service doesn't read selected model — FIXED
**File:** `backend/app/services/voice_service.py`
Added `_get_model(profile_id)` → reads `llm_model` from `settings_service.get()`.
Wired into `chat_completion`, `voice_pipeline`, `get_status`.

### 3. LLM parse error on Android client
Unknown. Possibly:
- Flutter failing to parse the chat response JSON
- Streaming mismatch (expecting different shape)
- Ollama returning error for model name mismatch (`phi4-mini` vs `phi4-mini:latest`)
- Check `client/lib/services/voice_service.dart` response handling

## Multi-Profile Refactor

### Conversation Memory — DONE
`ConversationMemory` → `ConversationMemoryManager` with per-profile JSON files.
`voice_service.py` uses `mem = conversation_memory.for_profile(profile_id)`.

### Personality Service — DONE
`PersonalityService` → multi-profile with `ProfileData` instances.
All methods accept `profile_id: str = "default"`.
**Fix applied:** `get_system_prompt(profile_id=)`, `get_status(profile_id=)` called from voice_service.

## Tailscale

### `asyncio.create_subprocess_exec` not supported on Windows — FIXED
**File:** `backend/app/services/tailscale_service.py`
Switched to `asyncio.to_thread(subprocess.run)` with `_run()` helper. Works cross-platform.

## Auth

### `require_auth` Header dependency
All settings routes require `Authorization: Bearer <token>`. Flutter client sends token from login.
Works — `GET /api/v1/auth/login` returns 200, token flows to subsequent requests.

## Startup Script

### `run-backend.ps1` — FIXED
Starts Ollama automatically, waits 3s, then starts uvicorn.
On exit (Ctrl+C), stops Ollama.
PowerShell execution policy blocks direct `.ps1` run — use `powershell -ExecutionPolicy Bypass -File run-backend.ps1`.

## Available Ollama Models
- `llama3.2:latest` (default)
- `phi4-mini:latest`
- `gemma4:e2b`
- `llava:7b`

## Next Debugging Steps
1. Test `POST /api/v1/voice/chat` directly with curl/PowerShell to confirm backend response shape
2. Check Flutter `voice_service.dart` response parsing
3. Test model switch → PATCH settings → verify `settings.json` updated on disk
4. Verify `_get_model()` picks up new value on next chat
