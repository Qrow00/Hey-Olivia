---
name: executing-plans
description: Use when you have a plan document to implement step by step
---

# Executing Plans

## Overview

Use when you have a plan and need to execute it step by step. Good for smaller plans, or when you want close control over implementation, or when your model is too small for subagent-driven development.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Rules:**
- Read the plan document carefully
- Implement each task in order
- Run tests at the end of each task
- Commit at the end of each task
- Execute **one task at a time** and **pause after each task** to update the plan doc and check in with the user (unless they said otherwise)
- Only the current task's checkbox gets `[x]` — completed tasks' steps keep `[x]` on each step too, but the task itself should reflect current state

## Plan Document Location

**Plans are saved to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Execution

### For Each Task

1. **Read the task** completely
2. **Implement** the task (if running in a git worktree, this happens there)
3. **Run tests** for the task
4. **Mark checkboxes** — update the plan document: mark this task's steps `[x]`
5. **Commit** the task (or at least make sure the worktree is clean)
6. **Check in with the user**: report what was done, whether tests pass, and note anything unexpected. If a task can't be completed, report the blocker and ask how to proceed rather than guessing.
7. **Next task** — proceed to the next task unless the user indicates otherwise

## Progress Updates

Keep the plan document up to date as you go. The plan document is your source of truth for what's done and what's next. Completed tasks' steps should have their checkboxes marked `[x]`.

## Scripts

If any of these apply:
- **Worktree:** Ensure the `superpowers:using-git-worktrees` skill is loaded before starting work.
- **Subagents:** If tasks would benefit from parallel implementation, use `superpowers:dispatching-parallel-agents` instead of executing inline.

## Context Management

To manage context, keep a "working notes" section at the bottom of your plan document. If your context window gets full, you can summarize completed tasks there, then open a fresh session. Let the plan document be your source of truth.

## Pausing Between Tasks

For anything but very small plans, always pause after each task. "Pausing" means ending your turn after a task is complete and asking the user to check in before continuing. This gives the user a chance to correct course, and lets you reorient before continuing.

## Plan Failures

If you find the plan failing during execution — a task that can't be done as written, contradictions, or missing pieces — **stop and flag it**. Don't improvise your way through. Report what failed, why, and suggest a fix. Let the user decide: fix the plan now or abort.

## Completion

When all tasks are done:
1. Update the plan document's checkboxes
2. Run the full test suite to confirm everything passes
3. Report completion, including which tasks were completed and any deviations from the plan
