---
title: Edge-TTS over Piper for TTS
date: 2026-07-19
tags: [decision, voice, tts]
type: decision
status: permanent
related: [[Voice Pipeline]], [[Voice Profile Service]]
---

## Context
Piper TTS was initially planned for local TTS. Needed natural-sounding voices with pitch/rate control.

## Decision
Used Edge-TTS (Microsoft Edge's online TTS API). No local model, but natural voices, pitch/rate params, and multiple voice profiles.

## Consequences
- Requires internet for TTS
- Natural voices with emotion
- Voice profiles (JARVIS, Friday, Edith, Tobby, Karen) trivially switchable
- Fallback: Chatterbox TTS planned for offline voice cloning
