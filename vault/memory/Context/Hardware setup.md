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
- Ollama for LLM (llama3.2, qwen2.5-coder, llava:7b) — GPU (verified on Ollama 0.32.4, see [[GTX 1050 CAN run Ollama on GPU — requires Ollama v0.12.0+]])
- Whisper for STT (CUDA)
- Connected via Tailscale to client devices

## Client machines
- Android phone/tablet (Flutter)
- Windows desktop (Flutter)
- Linux desktop (Flutter)

## GPU (NVIDIA GTX 1050)
- Pascal, compute capability 6.1, 4GB VRAM
- Supported by torch/CUDA for Whisper
- Ollama runs on GPU since v0.12.0 (native SM61 kernels); pre-0.12.0 forced the CPU runner
- Detected at startup by `hardware_detector.py` (nvidia-smi + torch + ollama version)
