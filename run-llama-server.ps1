<#>
.SYNOPSIS
    Launch llama.cpp llama-server for JARVIS V3 chat (OpenAI-compatible :8080).
.DESCRIPTION
    Serves the local GGUF model on http://127.0.0.1:8080/v1 so JARVIS can
    chat with real context. Always uses the GPU: Vulkan first (works on this
    GTX 1050 / Pascal card), then CUDA. Refuses to run on CPU unless -Cpu is
    passed explicitly.
.NOTES
    Usage: .\run-llama-server.ps1
    The backend picks this up via JARVIS_USE_LLAMA_SERVER=1 (run-backend.ps1).
#>

param(
    [string]$Model = "models\Llama-3.2-1B-Instruct-Q4_K_M.gguf",
    [int]$Port = 8080,
    [int]$CtxSize = 4096,
    [switch]$Cpu
)

$vulkanExe = Join-Path $PSScriptRoot "backend_new\models\llama.cpp-vulkan\llama-server.exe"
$cudaExe   = Join-Path $PSScriptRoot "backend_new\models\llama.cpp-cuda\llama-server.exe"
$cpuExe    = Join-Path $PSScriptRoot "backend_new\models\llama.cpp\llama-server.exe"
$modelFull = Join-Path $PSScriptRoot "backend_new\$Model"

if (-not (Test-Path $modelFull)) {
    Write-Warning "Model not found at $modelFull"
}

$exe = $null
if (-not $Cpu -and (Test-Path $vulkanExe)) {
    $exe = $vulkanExe
    Write-Host "Backend: Vulkan (GPU offload)" -ForegroundColor Green
} elseif (-not $Cpu -and (Test-Path $cudaExe)) {
    $exe = $cudaExe
    Write-Host "Backend: CUDA (GPU offload)" -ForegroundColor Green
} elseif ($Cpu -and (Test-Path $cpuExe)) {
    $exe = $cpuExe
    Write-Host "Backend: CPU (explicit -Cpu)" -ForegroundColor Yellow
} else {
    Write-Error "No GPU llama-server binary found (Vulkan or CUDA). CPU is disabled by policy."
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  JARVIS V3 - Local LLM (llama-server)" -ForegroundColor Cyan
Write-Host "  Exe: $exe" -ForegroundColor Green
Write-Host "  Model: $modelFull" -ForegroundColor Green
Write-Host "  Endpoint: http://127.0.0.1:$Port/v1" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

& $exe -m $modelFull --host 127.0.0.1 --port $Port -c $CtxSize --parallel 1 -ngl 999
