# Stop the brainstorm visual-companion server and clean up.
# Usage: stop-brainstorm.ps1 <session_dir>
#
# Kills the server process. Only deletes the session directory when it lives
# under the temp dir (ephemeral). Persistent directories (.superpowers/) are
# kept so mockups can be reviewed later.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SessionDir
)

$ErrorActionPreference = "Stop"
$stateDir = Join-Path $SessionDir "state"
$pidFile = Join-Path $stateDir "server.pid"
$idFile = Join-Path $stateDir "server-instance-id"

function Mark-Stopped([string]$Reason) {
    Remove-Item (Join-Path $stateDir "server-info") -Force -ErrorAction SilentlyContinue
    Set-Content -Path (Join-Path $stateDir "server-stopped") -Value ("{{""reason"":""{0}"",""timestamp"":{1}}}" -f $Reason, [DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
}

function Read-ServerId {
    if (-not (Test-Path $idFile)) { return $null }
    return (Get-Content $idFile -Raw).Trim()
}

if (-not (Test-Path $pidFile)) {
    Write-Output '{"status": "not_running"}'
    exit 0
}

$pidValue = (Get-Content $pidFile).Trim()
$proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue

if (-not $proc) {
    Remove-Item $pidFile, $idFile -Force -ErrorAction SilentlyContinue
    Mark-Stopped "stale_pid"
    Write-Output '{"status": "stale_pid"}'
    exit 0
}

# Prove this PID is our server: its command line must carry this start's
# instance id. Refuse to signal anything we can't confirm.
$expected = Read-ServerId
$cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $pidValue" -ErrorAction SilentlyContinue).CommandLine
if (-not $expected -or -not $cmdLine -or $cmdLine -notmatch [regex]::Escape("--brainstorm-server-id=$expected")) {
    Remove-Item $pidFile, $idFile -Force -ErrorAction SilentlyContinue
    Mark-Stopped "stale_pid"
    Write-Output '{"status": "stale_pid"}'
    exit 0
}

Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 200

Remove-Item $pidFile, $idFile, (Join-Path $stateDir "server.log") -Force -ErrorAction SilentlyContinue
Mark-Stopped "stop-brainstorm.ps1"

# Only delete ephemeral temp directories.
$tempRoot = [System.IO.Path]::GetFullPath($env:TEMP)
$sessionFull = [System.IO.Path]::GetFullPath($SessionDir)
if ($sessionFull.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    Remove-Item -Recurse -Force $SessionDir -ErrorAction SilentlyContinue
}

Write-Output '{"status": "stopped"}'
