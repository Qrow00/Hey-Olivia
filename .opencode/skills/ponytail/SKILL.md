---
name: ponytail
description: Use whenever writing, implementing, or reviewing code for this project — enforce the Minimalism Decision Ladder (YAGNI first, stdlib, native platform, existing deps, one line, minimum that works). Trigger on "keep it simple", "minimal", "don't over-engineer", "no new dependency", "YAGNI".
---

# Ponytail — Minimalism Decision Ladder

Before writing any code, descend this ladder. Stop at the first satisfied rung.

1. **YAGNI** — Skip it entirely. Don't build something you don't need right now.
2. **Use stdlib** — Can Python/Dart built-ins do this? No new dependency.
3. **Use native platform feature** — OS API, shell command, platform channel.
4. **Use existing dependency** — Already in `requirements.txt` or `pubspec.yaml`.
5. **Write one line** — Literally one expression. If it needs more, reconsider.
6. **Write the minimum that works** — No abstraction, no over-engineering, no comments.

## How to apply

- State which rung you stopped at before writing code (e.g. "rung 2 — stdlib `sqlite3`").
- If you propose a new dependency, cite the rung-4 existing option you checked first and why it can't do the job.
- No config files, base classes, registries, or "future-proofing" unless a current feature requires them.
- No comments unless the user asks for them.

## Review checklist (when reviewing existing code)

- [ ] Any code that does nothing today → delete (rung 1).
- [ ] Any dependency that could be replaced by stdlib or an OS command → remove.
- [ ] Any abstraction with exactly one use → inline it.
- [ ] Any "one day we might need X" code → gone.

## Examples

- Request: "add a settings API endpoint" → FastAPI already provides the router pattern → rung 4 (existing dependency), add the route only, no new service class.
- Request: "convert timestamps to readable strings" → use stdlib `datetime` → rung 2.
- Request: "cache API responses" → skip unless a current endpoint measurably needs it → rung 1.
