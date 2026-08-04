---
title: TEMPORARY — Laptop random shutdown diagnosis
date: 2026-08-03
updated: 2026-08-03
tags: [context, hardware, shutdown, reminder]
type: context
status: temporary
related: [[Memory Map]], [[Hardware setup]], [[System Monitoring]]
---

# TEMPORARY — Laptop random shutdown diagnosis

> **Reminder: pick this up on the next session.** This is an active diagnostic. Do not archive until resolved.

## Active task
Laptop (ASUS GL553VD, GTX 1050) shuts down unexpectedly mid-work, often multiple times per day. Next step is to capture a real-time log under load before the next shutdown.

## Known facts (verified Aug 3)
- **Windows Event Log:** 11× Event 41 (Kernel-Power, Bugcheck=0) in the last week — 3 today (12:40 AM, 6:38 PM, 6:54 PM). No WHEA errors, no BSOD → abrupt power loss.
- **Battery:** Simplo ICR18650, design 48,240 mWh but **full charge only 16,085 mWh = 33% health**, 33 cycles (age, not cycling, killed it). Life estimate ~24 min.
- **Always on AC** — every active session in the battery report is `Active / AC`, yet it still dies.

## Hypotheses (in order of likelihood)
1. **Thermal protection under load** — documented on this exact model: the "CPU" temperature sensor hits 96-100°C and the board hard-cuts power (matches Event 41 signature). Runs 80-89°C under load by design; fan/sensor behavior is known-flaky.
2. AC adapter / DC-in jack intermittency — a healthy battery would backstop AC dips; a 33% battery can't.
3. Battery / charging circuit dragging the power rail.

## Diagnostic tool built Aug 3
- `backend/tools/thermal_diag_logger.py` — standalone, logs CPU temp (WMI), GPU temp/load (nvidia-smi), CPU load, RAM, battery, `ac_plugged` every 5s to `data/logs/thermal_diag_*.tsv`, flushed per row so it survives sudden death. Also WMI shutdown-event watcher.
- Launcher: `run-thermal-logger.ps1` (use `powershell -ExecutionPolicy Bypass -File run-thermal-logger.ps1`).

## Load test Aug 3 (AI app as workload — DONE)
Ran backend (run-backend.ps1) + 12 rounds of sustained llama3.2 inference via Ollama (512 tok each, ~20 tok/s, ~6.5 min continuous GPU load).
- **Peak GPU temp: 85°C** at 100% load — plateaued, never reached the ~92°C throttle limit. **NO shutdown.**
- CPU WMI sensor stayed at ~36°C the entire time (may not reflect true CPU die temp — LLM inference is mostly GPU-bound).
- RAM peaked ~90% (8GB machine), battery 99%/AC constant.
- **Conclusion: pure AI-app load does NOT reproduce the shutdown.** GPU runs hot (84-85°C) but safe. Thermal likely NOT the trigger for this workload.
- Logger left running (`data/logs/thermal_diag_*.tsv`) to capture during normal use — check it if the laptop dies again.
- Next angle: shutdowns may need a heavier CPU-bound workload (compile/render/gaming), OR the AC-adapter/DC-jack path. Re-check last log rows before next death.

## Next step
Run the logger under the exact workload that kills the laptop, then read the last rows:
- Temps climbing to ~95-100°C before death → thermal protection → repaste + fan clean + undervolt.
- Healthy temps + instant death → AC/battery path → then test battery removal (CAUTION: GL553VD is known to sometimes refuse to boot on AC alone with no battery installed).
