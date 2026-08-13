<#>
.SYNOPSIS
    Launch J.A.R.V.I.S. V3 (Agent Core) Backend Server
.DESCRIPTION
    Starts the FastAPI backend: LLM-free NLU command path, optional chat model,
    personality sliders, skills, memory, learner, vision, WebSocket gateway.
.NOTES
    Requires: fastapi + uvicorn. Heavy deps (faster-whisper, edge-tts,
    openwakeword, opencv, onnxruntime) are optional and lazy-loaded.
    Set JARVIS_SERVICES to gate service groups (default: full).
    Set JARVIS_USE_LLAMA_SERVER=1 to chat through an OpenAI-compatible
    llama-server; otherwise JARVIS_CHAT_GGUF is loaded in-process when
    llama-cpp-python is available, else template fallback.
#>

param(
    [string]$Services = "full",
    [int]$Port = 8000,
    [string]$ModelPath = "models\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
)

# Self-locate: make the project root the working directory regardless of how
# this script is launched (Start-Process, Task Scheduler, WMI, etc).
Set-Location -LiteralPath $PSScriptRoot
$env:JARVIS_SERVICES = $Services
$env:JARVIS_USE_LLAMA_SERVER = "1"
$env:JARVIS_CHAT_API = "http://127.0.0.1:8080/v1"
$env:PYTHONPATH = "$PSScriptRoot\backend_new;$env:PYTHONPATH"

# Add scripts to PATH
$env:PATH += ";$env:APPDATA\Python\Python314\Scripts"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. V3 - Agent Core Launcher" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Services: $Services" -ForegroundColor Green
Write-Host "Port: $Port" -ForegroundColor Green
Write-Host "Model: $ModelPath" -ForegroundColor Green
Write-Host "Working Dir: $PSScriptRoot\backend_new" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

# Check if model exists
$modelFullPath = Join-Path (Join-Path $PWD "backend_new") $ModelPath
if (-not (Test-Path $modelFullPath)) {
    Write-Warning "Model not found at: $modelFullPath"
    Write-Warning "Chat will run in template fallback mode (commands still work)."
}

# Start the server
try {
    python -m uvicorn app.api.main:app --host 0.0.0.0 --port $Port
}
catch {
    Write-Error "Failed to start server: $_"
    Read-Host "Press Enter to exit"
}
