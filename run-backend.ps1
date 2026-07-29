param(
    [string]$Services = "all"
)

$mode = "J.A.R.V.I.S. Backend"
if ($Services -ne "all") {
    $mode += " [services: $Services]"
}

Write-Host "Starting $mode..." -ForegroundColor Cyan

# Start Ollama in background if not already running
$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaProcess) {
    Write-Host "[OLLAMA] Starting..." -ForegroundColor Yellow
    $null = Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep 3
    Write-Host "[OLLAMA] Ready" -ForegroundColor Green
} else {
    Write-Host "[OLLAMA] Already running" -ForegroundColor Green
}

$env:JARVIS_SERVICES = $Services
Set-Location "D:\project\Jarvis project\Hey-Olivia\backend"

try {
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
finally {
    Write-Host "[OLLAMA] Stopping..." -ForegroundColor Yellow
    $null = Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
    Write-Host "[OLLAMA] Stopped" -ForegroundColor Green
}
