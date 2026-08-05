---
title: Headroom context compression for opencode
date: 2026-08-05
tags: [learning, tooling, headroom, token-tracking, opencode]
type: learning
status: permanent
related: [[CodeBurn token usage tracker]], [[AGENTS]], [[Memory Map]]
source: https://github.com/headroomlabs-ai/headroom
---

## Problem
opencode sessions re-read large tool outputs (grep, LSP diagnostics, JSON) every turn, burning input tokens. Claude Code/Codex wrapped runs cost noticeably less than raw opencode runs on the same task.

## Solution
**Headroom** — local proxy/library that compresses what the agent reads before it reaches the LLM. Same answers, fewer tokens. 15-20% for coding agents, 60-95% for JSON tool output.

## Installed (2026-08-05)
- `pip install "headroom-ai[proxy]"` → `headroom-ai 0.33.0`
- Binary: `C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\headroom.exe` — NOT on PATH (pip user-site). Use full path.
- `uv` not installed on this machine; used pip instead of `uv tool install`.

## opencode integration
- `headroom wrap opencode` — starts proxy (port 8787), injects `headroom` provider via `@ai-sdk/openai-compatible`, registers headroom MCP (`headroom_compress`/`headroom_retrieve`/`headroom_stats`), backs up opencode config, launches opencode. Run from a fresh terminal (it launches opencode itself).
- `headroom unwrap opencode` — removes edits, restores `opencode.json.headroom-backup`.
- Proxy health: `curl http://localhost:8787/health`; savings: `curl http://localhost:8787/stats`; log summary: `headroom perf`.
- Windows: launch proxy detached with `Start-Process` so it survives the shell.

## Notes
- Default `coding` savings profile (cache mode) keeps Anthropic prefix-cache stable; `HEADROOM_SAVINGS_PROFILE=agent-90` for aggressive compression.
- `headroom_retrieve` MCP tool can fetch full uncompressed content by hash — lossless recovery path.
- Wired into opencode via `/headroom` command (`.opencode/command/headroom.md`) and the `headroom` skill (`.opencode/skills/headroom/SKILL.md`).
- Benchmarks (ritza-co/headroom-benchmark): ~-25% billed tokens on heavy tasks; savings scale with task size.
