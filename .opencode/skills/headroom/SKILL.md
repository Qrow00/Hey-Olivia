---
name: headroom
description: Use when the user wants to reduce token usage or compress opencode context — start the Headroom proxy, wrap/unwrap opencode through it, or check proxy savings/perf.
---

# Headroom — Context Compression for opencode

Compresses everything an agent reads (tool outputs, logs, files, conversation history) before it reaches the LLM. Typical savings: 15-20% for coding agents, 60-95% for JSON tool output. Same answers, fewer tokens. Local-first.

## Installed (this machine)

- Version: 0.33.0 (pip user-site, extra `[proxy]`)
- Binary: `C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\headroom.exe` — NOT on PATH, always use the full path.
- Proxy port: 8787 (default).

## Routing opencode through Headroom

`headroom wrap opencode` is the one-command integration:

1. Starts the proxy (unless `--no-proxy`).
2. Injects a `headroom` provider (via `@ai-sdk/openai-compatible`) pointed at the proxy.
3. Registers the headroom MCP server (`headroom_compress`, `headroom_retrieve`, `headroom_stats`).
4. Backs up `opencode.json` → `opencode.json.headroom-backup`.
5. Launches opencode.

Revert with `headroom unwrap opencode`. Run wrap from a fresh terminal — it launches opencode itself.

Flags: `--port`, `--no-mcp`, `--no-serena`, `--no-context-tool`, `--code-graph`, `--learn`, `--memory`, `--no-proxy`.

## Proxy operations

- Start: `headroom proxy --port 8787`
- Health: `curl http://localhost:8787/health`
- Savings: `curl http://localhost:8787/stats`
- Logs summary: `headroom perf`

## Notes

- Use the default `coding` savings profile (cache mode) for coding work; `HEADROOM_SAVINGS_PROFILE=agent-90` for aggressive compression.
- The `headroom_retrieve` MCP tool lets the agent fetch full uncompressed content when a compressed marker is ambiguous — never lose data, just tokens.
- On Windows launch the proxy detached so it outlives the shell: `Start-Process -FilePath "<headroom.exe>" -ArgumentList "proxy","--port","8787"`.
