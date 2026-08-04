---
title: Pinned Issues — Current Session (Jul 29)
date: 2026-07-29
updated: 2026-08-03
tags: [context, issues, debugging, llm]
type: context
status: permanent
related: [[AGENTS]], [[MASTER_PLAN]], [[Memory Map]]
---

## Backend Crashes

### Port conflict (Errno 10048) — LAST ERROR (verified Aug 1)
Old python process holds port 8000 after shell dies. Fix: `Stop-Process -Name python` before restart.
In `run-backend.ps1`: Ollama + lifecycle management implemented.
**Log check 2026-08-01:** Last error logged was `[Errno 10048]` port 8000 bind failure in `backend/server_err2.log` (Jul 29, 11:22). Non-fatal — second instance failed to bind while first kept serving. Most recent run (`backend/server_test_err.log`, Jul 31, 16:31) started clean and accepted a WebSocket on `/ws`. Watch for: if server unresponsive AND log shows 10048, nothing is listening on 8000.

## LLM Selection

### 1. Settings PATCH 307 Redirect — FIXED
**File:** `backend/app/routers/settings.py`
Changed all routes from `"/"` to `""` so FastAPI doesn't 307-redirect PATCH to `/api/v1/settings/`.
Flutter `http` package doesn't follow 307 for PATCH/verbs.

### 2. Voice service doesn't read selected model — FIXED
**File:** `backend/app/services/voice_service.py`
Added `_get_model(profile_id)` → reads `llm_model` from `settings_service.get()`.
Wired into `chat_completion`, `voice_pipeline`, `get_status`.

### 3. LLM parse error on Android client — NOT REPRODUCIBLE BACKEND-SIDE (verified Aug 3)
Investigated. All backend responses are correct:
- `POST /api/v1/voice/chat` → `{"response": "...", "model": "llama3.2", "done": true}` (tested)
- WebSocket `voice_response` → string fields `transcription`/`response`/`audio`/`model`
- Flutter `voice_service.dart` `_handleMessage` reads only string fields (`?? ''`) — no `fromJson` on chat responses; `home_screen.dart` just splits the response string
- Likely remaining suspects need a device test: TTS plugin playback path, stale app build, or an Android-only runtime error. No client code fix warranted without the actual error text.

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

## Ollama GPU + VRAM budget (Aug 3)

- **Ollama 0.32.4 runs the GTX 1050 on GPU** (native SM61 kernels since v0.12.0). The old "CPU forced" reality was self-inflicted: user env vars `OLLAMA_LLM_LIBRARY=cpu` + `OLLAMA_NUM_GPU=0` (now cleared) and `hardware_detector.py`'s `OLLAMA_MIN_COMPUTE_CAP=8.0`. See [[GTX 1050 CAN run Ollama on GPU — requires Ollama v0.12.0+]].
- `hardware_detector.py` now probes `ollama --version` (>= 0.12.0) + CC >= 6.0; `run-backend.ps1` only forces CPU when that fails and prints GPU engagement from the serve log (`backend/logs/ollama_serve_err.log`).
- Whisper STT: `base` → `tiny` (measured 293 MiB), torch capped at 50% VRAM, `empty_cache()` after each transcription. `stt_model` added to settings.
- **Measured combined peak: 2.5 GB** (whisper tiny + llama3.2:3b @ 2048 ctx) — under the 3 GB budget. New `vram_high` alert rule fires at 3072 MB.
- Gotcha: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` is NOT supported on Windows torch (warns and is ignored) — removed.

## Next Debugging Steps
1. Test `POST /api/v1/voice/chat` directly — **DONE, passes** (correct shape, model + response)
2. Check Flutter `voice_service.dart` response parsing — **DONE, no crash path found**; needs Android device test for the original error
3. Test model switch → PATCH settings → verify `settings.json` on disk — **DONE, passes** (llm_model persisted; no 307 on PATCH)
4. Verify `_get_model()` picks up new value — **DONE, passes** (switched to `phi4-mini`, confirmed in reply; reverted to `llama3.2`)
