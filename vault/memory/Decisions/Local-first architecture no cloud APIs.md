---
title: Local-first architecture (no cloud APIs)
date: 2026-07-18
tags: [decision, architecture, privacy]
type: decision
status: permanent
related: [[AGENTS]], [[ROADMAP]], [[Voice Pipeline]]
---

## Context
Personal assistant with sensitive data (screen content, conversations, health data). Cloud APIs would leak everything.

## Decision
Everything runs local: Ollama for LLM, Whisper for STT, Edge-TTS as only cloud dependency (no data sent beyond audio synthesis). No OpenAI, no Google AI.

## Consequences
- Complete privacy — no data leaves the LAN
- No API costs
- Requires capable local hardware (HP EliteDesk + GTX 1050)
- Quality ceiling is Ollama model size (CPU-run llama3.2 on 2GB)
