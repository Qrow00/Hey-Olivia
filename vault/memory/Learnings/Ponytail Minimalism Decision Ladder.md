---
title: Ponytail Minimalism Decision Ladder
date: 2026-07-29
tags: [learning, methodology, minimalism, coding]
type: learning
status: permanent
related: [[AGENTS]], [[CodeBurn token usage tracker]]
source: AGENTS.md
---

## Problem
Code tends toward over-engineering — unnecessary abstractions, dependencies, and complexity.

## Solution
Before writing any code, descend this ladder. Stop at the first satisfied rung:

1. **YAGNI** — Skip it entirely. Don't build something you don't need right now.
2. **Use stdlib** — Can Python/Dart built-ins do this? No new dependency.
3. **Use native platform feature** — OS API, shell command, platform channel.
4. **Use existing dependency** — Already in `requirements.txt` or `pubspec.yaml`.
5. **Write one line** — Literally one expression. If it needs more, reconsider.
6. **Write the minimum that works** — No abstraction, no over-engineering, no comments.

## Application
Always descend this ladder before any new code. Most things should stop at rung 1-3.
