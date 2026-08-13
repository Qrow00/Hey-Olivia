<#>
.SYNOPSIS
    Launch J.A.R.V.I.S. V3 Flutter Client
.DESCRIPTION
    Starts the Flutter desktop client connecting to J.A.R.V.I.S. V3 backend
.NOTES
    Requires: Flutter SDK, backend running on port 8000
#>

param(
    [string]$BackendHost = "localhost",
    [int]$BackendPort = 8000,
    [string]$ClientDir = "client_new"
)

$env:JARVIS_BACKEND_URL = "ws://${BackendHost}:${BackendPort}/ws"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. V3 - Client Launcher" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Backend: ${BackendHost}:${BackendPort}" -ForegroundColor Green
Write-Host "Client Dir: $ClientDir" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

if (-not (Test-Path $ClientDir)) {
    Write-Error "Client directory not found: $ClientDir"
    Read-Host "Press Enter to exit"
    exit 1
}

Set-Location $ClientDir

# Check Flutter
C:\tools\flutter\bin\flutter.bat --version

# Get dependencies
C:\tools\flutter\bin\flutter.bat pub get

# Run desktop client (Windows)
C:\tools\flutter\bin\flutter.bat run -d windows --dart-define=BACKEND_URL=ws://${BackendHost}:${BackendPort}/ws