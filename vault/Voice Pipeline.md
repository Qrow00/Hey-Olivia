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

### LLM (Language Model)
- **Primary:** llama3.2 (general conversation)
- **Vision:** llava:7b (screen/camera analysis)
- **Coding:** qwen2.5-coder:7b

## Voice Flow

```
User speaks → Whisper (STT) → Text → LLM → Response → edge-tts → Audio
```

## WebSocket Events
- `voice_chunk` — send audio to server
- `voice_response` — receive audio response
- `avatar_state` — sync avatar with voice state

## Related

- [[AGENTS]] — local model configuration
- [[DATA_STRUCTURE]] — VoiceSession schema
- [[API_DOCS]] — voice endpoints
- [[Memory Map]] — vault index
