# J.A.R.V.I.S. — opencode Instructions

Project architecture, structure, conventions, and local models are in **`vault/AGENTS.md`** (canonical source).

## TEMPORARY — Active Reminder (remove once resolved)

The user's laptop (ASUS GL553VD) shuts down randomly. See **`vault/memory/Context/Laptop random shutdown diagnosis.md`** — on the next session, act on it (run the thermal logger under load before the next shutdown).

## Backend Runtime

- ALWAYS run the backend externally — launch `run-backend.ps1` in its own detached PowerShell window via `Start-Process`, never in the opencode shell session.

## Superpowers Skills

The project vendors the obra/superpowers skill library in `.opencode/skills/` (adapted for opencode + Windows PowerShell). When starting a task, check for a matching skill BEFORE writing code and load it via the `skill` tool.

- **Bootstrap:** `using-superpowers` — always load it first when a task might match a skill. It lists the skill-first rule, priority order, and platform adaptations.
- Planning → `brainstorming`, `writing-plans`; Execution → `subagent-driven-development`, `executing-plans`, `test-driven-development`; QA/quality → `verification-before-completion`, `systematic-debugging`, `requesting-code-review`, `receiving-code-review`; Git → `using-git-worktrees`, `finishing-a-development-branch`; Concurrency → `dispatching-parallel-agents`; Meta → `writing-skills`.
- `superpowers:` skill references resolve to local skills in `.opencode/skills/`. opencode subagents run on the session model (no model field). This machine's PowerShell has a Restricted execution policy — run `.ps1` skill scripts via `powershell -NoProfile -ExecutionPolicy Bypass -File <script>`.

## gstack Workflow

Available skills (use `/skill-name` to activate):

**Planning:**
- `/office-hours` — product interrogation, reframing
- `/plan-ceo-review` — scope challenge, 10-star product thinking
- `/plan-eng-review` — architecture, data flow, test plans
- `/autoplan` — runs CEO → design → eng review automatically

**Build:**
- `/review` — staff engineer bug hunt, auto-fix
- `/investigate` — root-cause debugging
- `/qa` — browser-based QA testing

**Ship:**
- `/ship` — tests, coverage, push, open PR
- `/retro` — weekly retrospective

**Safety:**
- `/careful` — warns before destructive commands
- `/freeze` — lock edits to one directory
- `/guard` — full safety mode

## Available Commands

- `/common-ground` — validate project assumptions
- `/discovery/create` — create discovery document
- `/planning/epic-plan` — epic planning
- `/execution/execute-ticket` — execute a ticket
- `/retrospectives/complete-sprint` — sprint retro

## Vault Graph

The vault uses Obsidian wikilinks (`[[Note Name]]`) to connect related notes. When reading a vault file:
1. Note its title and section headings
2. Follow any `[[wikilinks]]` you encounter — they connect to related context
3. Traverse 2-3 hops deep when investigating a topic (e.g., `[[Voice Pipeline]]` → links to `[[Wake Word Service]]` → links to `[[openWakeWord over Whisper for wake word]]`)
4. Use `vault/memory/Memory Map.md` as the entry point — it links to every memory note
5. This works alongside Obsidian — no vault files are modified

## Ponytail — Minimalism Decision Ladder

Before writing any code, descend this ladder (stop at first satisfied rung):
1. **YAGNI** — Skip it entirely. Don't build something you don't need right now.
2. **Use stdlib** — Can Python/Dart built-ins do this? No new dependency.
3. **Use native platform feature** — OS API, shell command, platform channel.
4. **Use existing dependency** — Already in `requirements.txt` or `pubspec.yaml`.
5. **Write one line** — Literally one expression. If it needs more, reconsider.
6. **Write the minimum that works** — No abstraction, no over-engineering, no comments.

## Model Rules

- Use `ollama/qwen2.5-coder:7b` for code generation and review
- Use `ollama/llama3.2:latest` for conversation and planning
- Always verify local model availability before assuming GPU access
- GPU is detected at startup by `backend/app/services/hardware_detector.py` (nvidia-smi + torch). Since Ollama v0.12.0 the GTX 1050 (Pascal, CC 6.1) runs the LLM on GPU; the CPU runner is only forced when the installed Ollama predates v0.12.0 or the compute capability is below 6.0. Never hardcode GPU assumptions.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
