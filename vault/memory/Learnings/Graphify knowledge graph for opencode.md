---
title: Graphify knowledge graph for opencode
date: 2026-08-05
tags: [learning, tooling, graphify, knowledge-graph, opencode]
type: learning
status: permanent
related: [[CodeBurn token usage tracker]], [[Headroom context compression for opencode]], [[AGENTS]], [[Memory Map]]
source: https://github.com/Graphify-Labs/graphify
---

## Problem
Answering codebase questions means grepping raw files, burning tokens re-discovering structure the agent already explored in past sessions.

## Solution
**Graphify** — builds a queryable knowledge graph from the repo (code, docs) using local tree-sitter AST. No embeddings, no vector store. Query/path/explain return scoped subgraphs instead of raw grep output.

## Installed (2026-08-05)
- `pip install graphifyy` → `graphifyy 0.9.32`
- Binary: `C:\Users\toshi\AppData\Roaming\Python\Python314\Scripts\graphify.exe` — NOT on PATH.
- `graphify opencode install` → wrote `## graphify` section to AGENTS.md + `.opencode/plugins/graphify.js` (`tool.execute.before` nudge) + registered plugin in `.opencode/opencode.json`.
- Graph built: `graphify-out/graph.json` — 2445 nodes, 3687 edges, ~119 communities (local-only: `extract . --code-only` + `cluster-only . --no-viz --no-label`).
- Wired into opencode via `/graphify` command (`.opencode/command/graphify.md`) and `graphify` skill (`.opencode/skills/graphify/SKILL.md`).

## Workflow
- Codebase questions: `graphify query "<question>"`, `graphify path A B`, `graphify explain "X"`, `graphify affected "X"`, `graphify god-nodes`.
- After code changes: `graphify update .` (AST-only, no API cost); `--force` after refactors that delete code.
- Local-first: use `--code-only` / `--no-label` — no cloud LLM calls. Semantic pass only if explicitly opted in.
- Benign warnings: Flutter boilerplate (Runner/RunnerTests) mints duplicate node names; graph keeps first occurrence.
