# Extract one task's full text from an implementation plan into a file the
# implementer reads in one call, so the task text never has to be pasted
# through the controller's context.
#
# Usage: task-brief.ps1 PLAN_FILE TASK_NUMBER [OUTFILE]
# Default OUTFILE: <repo-root>/.superpowers/sdd/<plan-basename>/task-<N>-brief.md
param(
    [Parameter(Mandatory = $true)]
    [string]$Plan,
    [Parameter(Mandatory = $true)]
    [int]$TaskNumber,
    [string]$OutFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Plan)) {
    Write-Error "no such plan file: $Plan"
    exit 2
}

if (-not $OutFile) {
    $dir = & (Join-Path $PSScriptRoot "sdd-workspace.ps1") $Plan
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $OutFile = Join-Path $dir "task-$TaskNumber-brief.md"
}

$lines = Get-Content -Path $Plan
$inTask = $false
$inFence = $false
$out = New-Object System.Collections.Generic.List[string]

foreach ($line in $lines) {
    if ($line -match '^```') {
        $inFence = -not $inFence
    }
    if (-not $inFence -and $line -match '^#+\s+Task\s+([0-9]+)') {
        $n = [int]$Matches[1]
        if ($n -eq $TaskNumber) {
            $inTask = $true
        } elseif ($inTask) {
            $inTask = $false
        }
    }
    if ($inTask) {
        $out.Add($line)
    }
}

if ($out.Count -eq 0) {
    Write-Error "task $TaskNumber not found in $Plan (no heading matching 'Task $TaskNumber')"
    exit 3
}

Set-Content -Path $OutFile -Value ($out.ToArray()) -Encoding UTF8
Write-Output "wrote ${OutFile}: $($out.Count) lines"
