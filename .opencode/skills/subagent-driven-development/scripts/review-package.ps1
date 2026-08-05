# Generate a review package: commit list, stat summary, and the net diff with
# extended context, written to a file the reviewer reads in one call. Using
# the recorded per-task BASE (not HEAD~1) keeps multi-commit tasks intact.
#
# Usage: review-package.ps1 PLAN_FILE BASE HEAD [OUTFILE]
# Default OUTFILE: <repo-root>/.superpowers/sdd/<plan-basename>/review-<base7>..<head7>.diff
param(
    [Parameter(Mandatory = $true)]
    [string]$Plan,
    [Parameter(Mandatory = $true)]
    [string]$Base,
    [Parameter(Mandatory = $true)]
    [string]$Head,
    [string]$OutFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Plan)) {
    Write-Error "no such plan file: $Plan"
    exit 2
}

git rev-parse --verify --quiet $Base *> $null
if ($LASTEXITCODE -ne 0) { Write-Error "bad BASE: $Base"; exit 2 }
git rev-parse --verify --quiet $Head *> $null
if ($LASTEXITCODE -ne 0) { Write-Error "bad HEAD: $Head"; exit 2 }

if (-not $OutFile) {
    $dir = & (Join-Path $PSScriptRoot "sdd-workspace.ps1") $Plan
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $base7 = (git rev-parse --short $Base).Trim()
    $head7 = (git rev-parse --short $Head).Trim()
    $OutFile = Join-Path $dir "review-$base7..$head7.diff"
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# Review package: $Base..$Head")
[void]$sb.AppendLine()
[void]$sb.AppendLine("## Commits")
[void]$sb.AppendLine((git log --oneline "$Base..$Head" | Out-String))
[void]$sb.AppendLine("## Files changed")
[void]$sb.AppendLine((git diff --stat "$Base..$Head" | Out-String))
[void]$sb.AppendLine("## Diff")
[void]$sb.AppendLine((git diff -U10 "$Base..$Head" | Out-String))

Set-Content -Path $OutFile -Value $sb.ToString() -Encoding UTF8

$commits = (git rev-list --count "$Base..$Head").Trim()
$size = (Get-Item $OutFile).Length
Write-Output "wrote ${OutFile}: $commits commit(s), $size bytes"
