---
title: GTX 1050 CAN run Ollama on GPU — requires Ollama v0.12.0+
date: 2026-07-19
updated: 2026-08-03
tags: [learning, hardware, gpu]
type: learning
status: permanent
related: [[AGENTS]], [[Hardware setup]]
source: verified on 2026-08-03 with Ollama 0.32.4
---

## Status: SUPERSEDED (2026-08-03)

The GTX 1050 (Pascal, CC 6.1) **does** run Ollama on the GPU with Ollama **v0.12.0+**.
Native SM60/SM61 kernels were restored upstream (ollama/ollama#12316 fixed in 0.12.0,
Flash Attention for CC 6.x in ollama/ollama#16994), so no PTX JIT is needed anymore.

## Verified on this machine (Ollama 0.32.4, GTX 1050)

Server log with the CPU forcing removed:

```
inference compute library=CUDA compute=6.1 name=CUDA0 "NVIDIA GeForce GTX 1050"
common_params_fit_impl: CUDA0: 27 layers, 2296 MiB used, 1067 MiB free
llama_kv_cache: CUDA0 KV buffer size = 416.00 MiB
Flash Attention enabled
```

- All 27 layers offloaded to GPU.
- `llama3.2:3b` @ 4096 ctx ≈ **2.3 GB VRAM** (fits a 3-4 GB budget, leaves ~1 GB for Whisper).
- Driver CUDA 13, Ollama picks `cuda_v12` library.

## Why it appeared broken before

The CPU forcing was NOT a real hardware limit. It came from:

1. `OLLAMA_LLM_LIBRARY=cpu` + `OLLAMA_NUM_GPU=0` set as **User** env vars and in
   `run-backend.ps1` / `hardware_detector.py` (`OLLAMA_MIN_COMPUTE_CAP` default 8.0).
2. Pre-0.12.0 Ollama builds shipped CUDA 13 PTX that CC 6.1 cannot JIT
   (`CUDA error: PTX was compiled with an unsupported toolchain`, exit 0xc0000409).

## Gotchas

- The Windows tray app (`ollama app.exe`) owns the server and respawns it. Setting
  `OLLAMA_LLM_LIBRARY` in a process env is ignored if the tray server is already up —
  kill `ollama app`, `ollama`, and `llama-server` before starting a clean `ollama serve`.
- User-scope env vars persist across sessions; clear them to un-force CPU.
- `ollama ps` PROCESSOR column shows `100% CPU` if the server inherited the forcing vars.

## Current state (Aug 3)

- User-scope `OLLAMA_LLM_LIBRARY` / `OLLAMA_NUM_GPU` cleared.
- `hardware_detector.py` probes Ollama version (>= 0.12.0) instead of assuming CC < 8.0 = CPU.
- `run-backend.ps1` only forces the CPU runner when the probe fails.
