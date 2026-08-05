---
title: CodeBurn token usage tracker
date: 2026-07-29
tags: [learning, tooling, codeburn, token-tracking]
type: learning
status: permanent
related: [[AGENTS]], [[Memory Map]]
source: https://github.com/getagentseal/codeburn
---

## Problem
AI coding token usage and cost across multiple tools (Claude Code, Cursor, Codex, OpenCode, etc.) is opaque. Bills show totals but not breakdowns by model, project, task, or tool.

## Solution
**CodeBurn** — free, open-source, local-first token/cost tracker. Reads session files already on disk from 36+ AI tools. No API keys, no upload.

### Quick start
```bash
npx codeburn          # interactive TUI dashboard (last 7 days)
npx codeburn web      # browser dashboard at localhost:4747
npm install -g codeburn  # permanent install
```

### Key commands
- `codeburn` — dashboard
- `codeburn today` / `codeburn month` — period reports
- `codeburn overview` — plain-text monthly summary
- `codeburn optimize` — find waste (re-reads, low read:edit, ghost agents, unused MCP servers)
- `codeburn optimize --apply` — auto-fix config waste with undo support
- `codeburn compare` — side-by-side model comparison (one-shot rate, cost per edit, cache hit rate)
- `codeburn yield` — productive vs abandoned spend (correlated with git commits)
- `codeburn guard install` — budget caps (soft/hard) for Claude Code sessions
- `codeburn mcp` — MCP server so agents can ask about spend mid-conversation
- `codeburn web` — local browser dashboard with charts
- `codeburn menubar` — macOS menu bar app

### Supported providers (that apply here)
- **OpenCode** (`~/.local/share/opencode/`) — SQLite sessions
- **Claude Code** (`~/.claude/projects/`) — JSONL sessions

### Waste detection
- Files re-read across sessions
- Low Read:Edit ratio (retries = wasted tokens)
- Uncapped bash output
- Unused MCP servers
- Ghost agents/skills never invoked
- Bloated CLAUDE.md files

## Application
Run `npx codeburn` from project directory to track Hey-Olivia's token usage. Use `codeburn optimize` periodically to find waste patterns. Use `codeburn yield` to see what spend actually shipped.

## Implemented (2026-08-05)
- Installed globally via npm: `codeburn@0.9.19` → `C:\Users\toshi\AppData\Roaming\npm\codeburn.cmd`. Node 24.19.0 meets the 22.13+ requirement.
- Windows quirk: the `.ps1` shim is blocked by PowerShell execution policy — always invoke `codeburn.cmd` (full path).
- Reads opencode sessions from `%USERPROFILE%\.local\share\opencode\opencode.db` (verified: 3 sessions).
- Wired into opencode via `/codeburn` command (`.opencode/command/codeburn.md`) and the `codeburn` skill (`.opencode/skills/codeburn/SKILL.md`).
