---
title: Hardware setup
date: 2026-07-18
updated: 2026-07-27
tags: [context, hardware, deployment]
type: context
status: permanent
related: [[AGENTS]], [[SETUP]]
---

## Server (HP EliteDesk)
- Runs FastAPI backend
- Ollama for LLM (llama3.2, qwen2.5-coder, llava:7b)
- Whisper for STT
- Connected via Tailscale to client devices

## Client machines
- Android phone/tablet (Flutter)
- Windows desktop (Flutter)
- Linux desktop (Flutter)

## GPU (AMD RX 6600)
- RDNA 2, 8GB VRAM
- No CUDA
- ROCm works on Linux, limited on Windows
- Limits: 7B param models, CPU fallback for Whisper
