# Start the brainstorm visual-companion server detached and output connection info.
# Usage:
#   start-brainstorm.ps1 [-ProjectDir <path>] [-Host <bind-host>] [-UrlHost <display-host>]
#                        [-IdleTimeoutMinutes <n>] [-Open] [-Foreground]
#
# Starts `node server.cjs` on a random high port, outputs the server-started JSON
# with the URL (which carries a per-session ?key=). Each session gets its own
# directory to avoid conflicts.
[CmdletBinding()]
param(
    [string]$ProjectDir,
    [string]$Host = "127.0.0.1",
    [string]$UrlHost = "",
    [int]$IdleTimeoutMinutes = 240,
    [switch]$Open,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($IdleTimeoutMinutes -lt 1) {
    Write-Output '{"error": "--IdleTimeoutMinutes must be a positive integer"}'
    exit 1
}
if (-not $UrlHost) {
    $UrlHost = if ($Host -eq "127.0.0.1" -or $Host -eq "localhost") { "localhost" } else { $Host }
}

# Unique session directory; persist under the project when asked so mockups
# survive restarts (and the port/token files let a restart reuse the same URL).
$sessionId = "$PID-$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
if ($ProjectDir) {
    $brainDir = Join-Path $ProjectDir ".superpowers\brainstorm"
    New-Item -ItemType Directory -Force -Path $brainDir | Out-Null
    $sessionDir = Join-Path $brainDir $sessionId
} else {
    $sessionDir = Join-Path $env:TEMP "brainstorm-$sessionId"
}
$contentDir = Join-Path $sessionDir "content"
$stateDir = Join-Path $sessionDir "state"
New-Item -ItemType Directory -Force -Path $contentDir | Out-Null
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

# Per-start instance id so the stop script can prove a PID is our server
# before signalling it (stale pid files point at unrelated processes).
$serverId = -join ((1..24) | ForEach-Object { "{0:x}" -f (Get-Random -Maximum 16) })
Set-Content -Path (Join-Path $stateDir "server-instance-id") -Value $serverId

$pidFile = Join-Path $stateDir "server.pid"
$logFile = Join-Path $stateDir "server.log"
$errFile = Join-Path $stateDir "server.err"

# Env consumed by server.cjs; a child process inherits the current environment.
$env:BRAINSTORM_DIR = $sessionDir
$env:BRAINSTORM_HOST = $Host
$env:BRAINSTORM_URL_HOST = $UrlHost
$env:BRAINSTORM_IDLE_TIMEOUT_MS = ($IdleTimeoutMinutes * 60 * 1000).ToString()
if ($Open) { $env:BRAINSTORM_OPEN = "1" }
if ($ProjectDir) {
    $env:BRAINSTORM_PORT_FILE = Join-Path $brainDir ".last-port"
    $env:BRAINSTORM_TOKEN_FILE = Join-Path $brainDir ".last-token"
}

# Kill any existing server for this session dir (stale from a crashed run).
if (Test-Path $pidFile) {
    $old = (Get-Content $pidFile) -as [int]
    if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $old -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

$node = "node"
if (-not (Get-Command $node -ErrorAction SilentlyContinue)) {
    Write-Output '{"error": "node not found on PATH — the visual companion needs Node.js"}'
    exit 1
}

if ($Foreground) {
    & $node "server.cjs" "--brainstorm-server-id=$serverId"
    exit $LASTEXITCODE
}

$server = Start-Process -FilePath $node -ArgumentList @("server.cjs", "--brainstorm-server-id=$serverId") `
    -WorkingDirectory $scriptDir -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile
Set-Content -Path $pidFile -Value $server.Id

# Wait for the server-started line (up to ~5s).
$started = $null
for ($i = 0; $i -lt 50; $i++) {
    if ($server.HasExited) { break }
    if (Test-Path $logFile) {
        $line = Select-String -Path $logFile -Pattern "server-started" -SimpleMatch | Select-Object -First 1
        if ($line) { $started = $line.Line; break }
    }
    Start-Sleep -Milliseconds 100
}

if ($started) {
    Write-Output $started
} else {
    $err = if (Test-Path $errFile) { (Get-Content $errFile -Raw).Trim() } else { "" }
    if ([string]::IsNullOrWhiteSpace($err)) {
        Write-Output '{"error": "Server failed to start within 5 seconds"}'
    } else {
        $detail = $err | ConvertTo-Json -Compress
        Write-Output ("{{""error"": ""Server failed to start within 5 seconds"", ""detail"": {0}}}" -f $detail)
    }
    exit 1
}
