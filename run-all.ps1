<#>
.SYNOPSIS
    Launch J.A.R.V.I.S. V3 Complete System (Backend + Client)
.DESCRIPTION
    Starts both backend and client in separate windows
.NOTES
    Opens two separate PowerShell windows
#>

param(
    [string]$Services = "minimal",
    [int]$Port = 8000
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. V3 - Full System Launcher" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Start backend in new window
$backendScript = Join-Path $PSScriptRoot "run-backend.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File", "`"$backendScript`"", "-Services", $Services, "-Port", $Port -WindowStyle Normal

# Wait for backend to start
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start client in new window
$clientScript = Join-Path $PSScriptRoot "run-client.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File", "`"$clientScript`"" -WindowStyle Normal

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "J.A.R.V.I.S. V3 launched successfully!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan