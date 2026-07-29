---
title: RX 6600 RDNA 2 limitations (no CUDA, limited ROCm)
date: 2026-07-19
tags: [learning, hardware, gpu]
type: learning
status: permanent
related: [[AGENTS]]
source: experimentation and install attempts
---

## Problem
RX 6600 is RDNA 2. No CUDA cores. ROCm on Windows is experimental and unstable. Whisper and Ollama default to CUDA.

## Solution
- Ollama works on RDNA 2 via ROCm backend (HIP) — works on Linux, limited on Windows
- Whisper works on CPU (slow but usable) or via DirectML (experimental)
- For production: use CPU for Whisper (base model), Ollama uses GPU via ROCm
- 8GB VRAM means 7B param models max for Ollama (quantized)

## Application
Always check `torch.cuda.is_available()` before assuming GPU. Set `_device = "cuda"` only if true. Default to CPU for STT.
