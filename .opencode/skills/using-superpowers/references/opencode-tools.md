# OpenCode Tool Mapping

This port of Superpowers runs on OpenCode. The skills speak in generic actions
("create a todo", "dispatch a subagent", "read a file"); this is how those
resolve to OpenCode's tools.

## Tool Mapping

- "Create a todo" / "mark complete in todo list" → `todowrite`
- "Dispatch a subagent" → `task` tool with `subagent_type: "general"`
  (or `"explore"` for codebase exploration). All templates in this port use
  `task`. Multiple `task` calls in one message run in parallel; one per
  response runs sequentially.
- "Invoke a skill" → the `skill` tool. `superpowers:<name>` = the skill named
  `<name>` in this library.
- "Read a file" → `read`
- "Create a file" / "edit a file" / "delete a file" → `write` / `edit` /
  `apply_patch`; for small diffs `apply_patch` is preferred.
- "Run a shell command" → `bash` (PowerShell 5.1 on Windows — see below)
- "Search file contents" / "find files by name" → `grep`, `glob`
- "Fetch a URL" → `webfetch`
- Subagent reuse: keep an implementer subagent's `task_id` from its dispatch
  result and pass it back to the `task` tool to resume it for fix rounds 1-3
  (see subagent-driven-development). Reviewers are one-shot; close them by not
  reusing their `task_id`.

## Model Selection Note

The templates in subagent-driven-development and requesting-code-review name a
`model:` per dispatch. OpenCode subagents run on the session's configured
model, so the `model:` field is dropped from the templates; treat Model
Selection in the SKILL.md as guidance on which subagent tier to use. If your
opencode config defines multiple agents, dispatch reviewers on the configured
review agent when one exists.

## Worktrees

OpenCode has no native worktree tool. `using-git-worktrees` Step 1a does not
apply — always use the Step 1b git worktree fallback.

## Windows / PowerShell Notes

- The shell is Windows PowerShell 5.1. Scripts shipped with the skills are
  `.ps1`, invoked as `& path/to/script.ps1 <args>` or
  `powershell -NoProfile -File path/to/script.ps1 <args>`.
- Environment detection uses the same read-only git commands; PowerShell
  equivalents of the bash one-liners are fine (`git rev-parse --git-dir`,
  `git rev-parse --git-common-dir`, `git branch --show-current`).
- Background servers (e.g. the brainstorming visual companion) must be started
  detached with `Start-Process` so they survive across turns; see the skill's
  scripts.

## Environment Detection

```powershell
$gitDir = git rev-parse --git-dir
$gitCommon = git rev-parse --git-common-dir
$branch = git branch --show-current
```

- `$gitDir != $gitCommon` → already in a linked worktree (skip creation)
- `$branch` empty → detached HEAD (cannot branch/push/PR normally)

See `using-git-worktrees` Step 0 and `finishing-a-development-branch` for how
each skill uses these signals.
