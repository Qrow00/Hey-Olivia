# Resolve and ensure the working-tree directory SDD uses for one plan's
# short-lived artifacts: task briefs, implementer reports, review packages,
# and the progress ledger. Prints the plan directory's absolute path.
#
# One directory per plan (.superpowers/sdd/<plan-basename>/) so a follow-up
# plan in the same working tree can never read or overwrite another plan's
# artifacts.
#
# The workspace lives in the working tree (not under .git/) so subagents can
# write their report files there. A self-ignoring .gitignore at
# .superpowers/sdd/ keeps every plan's workspace out of `git status` and out
# of accidental commits without modifying any tracked file.
#
# Single source of truth for the workspace location, so task-brief and
# review-package cannot drift to different directories.
#
# Usage: sdd-workspace.ps1 PLAN_FILE
param(
    [Parameter(Mandatory = $true)]
    [string]$Plan
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Plan)) {
    Write-Error "no such plan file: $Plan"
    exit 2
}

$slug = [System.IO.Path]::GetFileNameWithoutExtension($Plan)
if ([string]::IsNullOrWhiteSpace($slug)) {
    Write-Error "cannot derive a workspace name from: $Plan"
    exit 2
}

$root = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    Write-Error "not inside a git working tree"
    exit 2
}

$base = Join-Path $root ".superpowers\sdd"
$dir = Join-Path $base $slug
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Set-Content -Path (Join-Path $base ".gitignore") -Value "*"
Write-Output $dir
