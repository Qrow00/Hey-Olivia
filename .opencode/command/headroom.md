---
description: Manage the Headroom context-compression proxy for opencode (start proxy, wrap/unwrap opencode, check savings, view perf).
agent: general
---

Headroom compresses tool outputs and stale context before they reach the LLM, cutting token spend while keeping answers equivalent. Installed via pip (user site) — the binary is NOT on PATH.

Binary: `C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\headroom.exe`

Request/args: $ARGUMENTS

- `proxy` — start the proxy on port 8787. Launch detached so it stays up: `Start-Process -FilePath "C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\headroom.exe" -ArgumentList "proxy","--port","8787"`.
- `wrap opencode` — start/reuse the proxy, inject the headroom provider into opencode config, register the headroom MCP server, and launch opencode wrapped. MUST run from a fresh terminal (it launches opencode itself), not from inside this session.
- `unwrap opencode` — remove headroom config edits and restore the pre-wrap backup.
- `perf` — summarize savings from proxy logs.
- `mcp serve` — headroom MCP server (`headroom_compress`, `headroom_retrieve`, `headroom_stats`), used by the `wrap` command.

Always verify health first: `curl http://localhost:8787/health` → `{"status":"healthy",...}`. Check savings with `curl http://localhost:8787/stats`.

Remember `headroom.exe` is not on PATH in PowerShell — always use the full path above.
