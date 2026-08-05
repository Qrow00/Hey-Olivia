---
description: Run Graphify knowledge-graph commands for this project (query, path, explain, affected, god-nodes, update, extract).
agent: general
---

Run Graphify against the Hey-Olivia knowledge graph at `graphify-out/graph.json` (2445 nodes, ~119 communities).

Binary (pip user-site, NOT on PATH): `C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\graphify.exe`

Request/args: $ARGUMENTS

- No args → run `graphify god-nodes` to show architectural hubs.
- Common: `query "<question>"`, `path "<A>" "<B>"`, `explain "<concept>"`, `affected "<X>"`, `god-nodes`.
- After code changes: `update .` (AST-only, no API cost) or `extract . --code-only` for a full rebuild.
- Keep it local: use `--code-only` and `--no-label` — this project avoids cloud LLM calls.
- If `graphify-out/graph.json` is missing, rebuild: `extract . --code-only` then `cluster-only . --no-viz --no-label`.

Summarize the returned subgraph for the user rather than dumping raw output.
