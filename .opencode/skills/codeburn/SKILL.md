---
name: codeburn
description: Use when the user asks about AI token usage, cost, spend, or waste for opencode sessions — run CodeBurn reports (dashboard, today, month, overview, web, doctor, optimize, compare, yield, export).
---

# CodeBurn — Token/Cost Tracker

Local-first token/cost tracker for AI coding tools. Reads opencode's own session data on disk — no API keys, no upload. Supports 36+ tools (opencode, Claude Code, Cursor, Codex, etc.).

## Installed (this machine)

- Version: 0.9.19 (global npm)
- Binary: `C:\Users\toshi\AppData\Roaming\npm\codeburn.cmd`
- Use the `.cmd` shim — the `.ps1` shim is blocked by the PowerShell execution policy.
- Data read from: `%USERPROFILE%\.local\share\opencode\opencode.db` (3 sessions detected as of Aug 2026).

## Key commands

- `codeburn` — interactive TUI dashboard (last 7 days)
- `codeburn web` — browser dashboard at localhost:4747
- `codeburn today` / `codeburn month` — period reports
- `codeburn overview` — plain-text monthly summary
- `codeburn doctor [--provider opencode]` — verify data sources
- `codeburn optimize` — find waste (re-reads, low read:edit, ghost agents, unused MCP servers)
- `codeburn compare` — side-by-side model comparison
- `codeburn yield` — productive vs abandoned spend
- `codeburn export` — machine-readable data

`--provider opencode` filters to opencode sessions on most subcommands.

## Windows notes

- Interactive TUI commands may hang in a non-interactive shell — prefer `overview`/`today`/`month`/`doctor`/`optimize`/`export`, or launch the TUI detached via `Start-Process`.
- Requires Node.js 22.13+ (this machine: 24.19.0).

## Usage

Run the report the user asked for, then summarize tokens/cost/top models/waste. Suggest `codeburn optimize` periodically and `codeburn yield` to see what spend actually shipped.
