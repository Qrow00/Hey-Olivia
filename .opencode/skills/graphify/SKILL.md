---
name: graphify
description: Use when answering codebase questions or navigating this project — query the knowledge graph at graphify-out/ (graphify query, path, explain, affected, god-nodes) instead of grepping raw files. Also use after code changes to run graphify update to keep the graph fresh.
---

# Graphify — Knowledge Graph for Hey-Olivia

A queryable knowledge graph of the whole repo (backend, client, vault) built with local tree-sitter AST — no embeddings, no API calls for code. Read the graph before reading raw files for codebase questions.

## Installed (this machine)

- Version: 0.9.32 (pip, `graphifyy`)
- Binary: `C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\graphify.exe` — NOT on PATH.
- Graph: `graphify-out/graph.json` — 2445 nodes, 3687 edges, ~119 communities (built 2026-08-05).
- Installed for opencode: `AGENTS.md` section + `.opencode/plugins/graphify.js` (`tool.execute.before` nudge), registered in `.opencode/opencode.json`.

## Query commands

- `graphify query "<question>"` — BFS traversal, scoped subgraph (default 2000-token budget; `--budget N` to raise).
- `graphify path "<A>" "<B>"` — shortest path between two nodes.
- `graphify explain "<concept>"` — node + its neighbors.
- `graphify affected "<X>"` — reverse traversal: what is impacted by X.
- `graphify god-nodes` — most connected nodes (architectural hubs).
- `graphify tree` — D3 collapsible HTML tree.

## Keeping it current

- After modifying code: `graphify update .` (AST-only, no API cost). Use `--force` after refactors that delete code.
- Rebuild from scratch: `graphify extract . --code-only` then `graphify cluster-only . --no-viz --no-label` (keeps it fully local).
- `GRAPH_REPORT.md` exists for broad architecture; prefer scoped `query`/`path`/`explain` for focused questions.

## Local-first constraints

- This project is local-first (no cloud APIs). Use `--code-only` / `--no-label` so nothing leaves the machine. Skip the LLM semantic pass unless the user explicitly opts in.
