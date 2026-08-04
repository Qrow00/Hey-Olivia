# Project Memory

## Identity
- **Project:** J.A.R.V.I.S. — Personal AI Assistant
- **Path:** `D:\project\Jarvis project\Hey-Olivia`
- **Stack:** FastAPI (Python) + Flutter (Dart)
- **Git:** `https://github.com/Qrow00/Hey-Olivia.git` — `main` branch

## Status
- **MVP Phases 1–6:** ✅ COMPLETE
- **Enhancement Plan (all 8 phases):** ✅ COMPLETE
- **Last feature:** openWakeWord + two-phase voice + hardware detection (Jul 27)

## Quick start
- Backend: `.\run-backend.ps1` (uvicorn on port 8000)
- Client: `.\run-client.ps1` (flutter run)
- Flutter: `C:\flutter\bin`

## Run modes (JARVIS_SERVICES env var)
Set `$env:JARVIS_SERVICES` to control what loads:
- `all` (default) — everything: monitoring, browser, plugins
- `api` — API skeleton only, no background services — `.\run-backend-light.ps1`
- `api,monitoring` — API + monitoring/alerting
- `api,browser` — API + Playwright browser
- `api,monitoring,browser` — API + monitoring + browser (no plugins)

All route handlers are always registered regardless of mode.

## Memory (vault)
Persistent knowledge lives in the vault. Read these at session start:

### Canonical project info
- `vault/AGENTS.md` — architecture, structure, all 22 services, conventions, local models
- `vault/ROADMAP.md` — phase completion status
- `vault/memory/Memory Map.md` — full index of all memory notes

### Decisions, learnings, context
- `vault/memory/Decisions/` — architectural decisions with rationale
- `vault/memory/Learnings/` — debugging findings, tool gotchas
- `vault/memory/Context/` — project scope, hardware setup
- `vault/memory/Inbox/` — unprocessed memories (review each session)

### Feature documentation
- See `vault/memory/Memory Map.md` for the full table of feature docs (Voice Pipeline, Smart Home, Camera & Vision, etc.)

## Session flow
1. Read `vault/memory/Memory Map.md` for context
2. Read `vault/AGENTS.md` for project rules
3. Check `vault/memory/Inbox/` for pending items
4. At end of session: promote inbox items to permanent notes
