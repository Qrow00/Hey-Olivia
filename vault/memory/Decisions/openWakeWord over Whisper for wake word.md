---
title: openWakeWord over Whisper for wake word
date: 2026-07-27
tags: [decision, voice, wake-word]
type: decision
status: permanent
related: [[Voice Pipeline]]
---

## Context
Initial wake word used Whisper tiny model running on a continuous audio buffer — high latency (~1-2s) and 2GB+ VRAM from torch.

## Decision
Switched to openWakeWord with ONNX runtime. Lightweight (~50MB), <200ms detection, CPU-only.

## Consequences
- Near-instant wake detection
- Frees GPU VRAM for Whisper STT
- Prebuilt models: "hey jarvis", "alexa", "hey mycroft"
- No custom training possible without fine-tuning pipeline

## Update (2026-08-05): streaming voice loop

openWakeWord is now the core of a server-driven streaming voice loop, replacing the post-hoc whole-clip classification (`process_bytes` on entire utterances). The server runs one `VoiceSession` state machine per WebSocket connection (`backend/app/services/voice_session_service.py`) with phases LISTENING → COMMAND → THINKING → SPEAKING: openWakeWord detects the wake word frame-by-frame (1280 samples/80ms), Silero VAD endpoints the command, STT/LLM/TTS run server-side, and the wake model stays active during playback so re-detection barge-in interrupts TTS. The client is a thin pump streaming 16kHz s16 PCM frames. The old whole-clip wake-word service file was deleted.

Design: [2026-08-05 voice-mode-openwakeword design](../../../docs/superpowers/specs/2026-08-05-voice-mode-openwakeword-design.md)
