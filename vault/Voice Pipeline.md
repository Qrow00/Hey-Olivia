# Voice Pipeline

## Overview
JARVIS uses a voice-first interface with local processing for privacy and speed.

## Components

### STT (Speech-to-Text)
- **Engine:** Whisper (local, CPU)
- **Model:** base
- **File:** `backend/app/services/voice_service.py`

### TTS (Text-to-Speech)
- **Primary:** edge-tts (Microsoft)
- **Future:** Chatterbox TTS (Phase 8 — voice cloning)
- **Voices:** Configurable per profile

### Voice Session
- **Engine:** openWakeWord (`hey_jarvis`) + Silero VAD, per-connection
- **File:** `backend/app/services/voice_session_service.py`
- **Role:** owns the full streaming voice loop — one `VoiceSession` state machine per WebSocket connection

### LLM (Language Model)
- **Primary:** llama3.2 (general conversation)
- **Vision:** llava:7b (screen/camera analysis)
- **Coding:** qwen2.5-coder:7b

## Voice Flow

The client is a thin audio pump: while wake-word mode is active it streams
continuous 16kHz mono s16 PCM to the server via `audio_frame`. The server owns
the loop in a per-connection `VoiceSession`:

```
LISTENING → COMMAND → THINKING → SPEAKING → LISTENING
```

1. **LISTENING** — openWakeWord scores frames one at a time (1280 samples / 80ms). Above threshold → `wake_word_detected` → **COMMAND**; frames after detection flow straight into the command buffer (one-breath commands).
2. **COMMAND** — Silero VAD (480-sample chunks) detects onset and offsets speech → **THINKING** → STT → command registry / LLM → TTS → `voice_response` → **SPEAKING**.
3. **SPEAKING** — wake model stays active; re-detection interrupts playback (barge-in). On client `tts_done` → **LISTENING**. Wake word is required every turn.

## WebSocket Events
- `voice_mode_start` — start session; stream after `voice_mode_ready`
- `audio_frame` — stream raw s16 PCM (base64)
- `tts_done` — playback finished → server returns to LISTENING
- `voice_mode_stop` — tear down session
- `voice_mode_ready` / `voice_phase` — session state sync from server
- `wake_word_detected` — wake word heard (also barge-in during playback)
- `voice_response` — receive audio response
- `avatar_state` — sync avatar with voice state
- `voice_error` — error notification

## Related

- [[AGENTS]] — local model configuration
- [[DATA_STRUCTURE]] — VoiceSession schema
- [[API_DOCS]] — voice endpoints
- [[Memory Map]] — vault index
