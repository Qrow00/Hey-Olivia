---
title: openWakeWord over Whisper for wake word
date: 2026-07-27
tags: [decision, voice, wake-word]
type: decision
status: permanent
related: [[Voice Pipeline]], [[Wake Word Service]]
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
