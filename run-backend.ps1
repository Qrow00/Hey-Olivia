param(
    [string]$Services = "all"
)

$mode = "J.A.R.V.I.S. Backend"
if ($Services -ne "all") {
    $mode += " [services: $Services]"
}

Write-Host "Starting $mode..." -ForegroundColor Cyan

# Detect GPU and configure Ollama based on actual hardware. Since Ollama v0.12.0
# native SM60/61 kernels make the GTX 1050 (Pascal, CC 6.1) fully GPU-capable, we
# only force the CPU runner when the installed Ollama predates that or the GPU is
# too old. The detector probes `ollama --version` and the detected compute cap.
$backendPy = "D:\project\Jarvis project\Hey-Olivia\backend\.venv\Scripts\python.exe"
$detector = "backend\app\services\hardware_detector.py"
if (Test-Path $detector) {
    $lib = & $backendPy -c "import sys; sys.path.insert(0, 'backend'); from app.services import hardware_detector as hd; print(hd.ollama_llm_library())"
    if ($lib -eq "cpu") {
        Write-Host "[OLLAMA] GPU acceleration unavailable - forcing CPU runner" -ForegroundColor Yellow
        $env:OLLAMA_NUM_GPU = "0"
        $env:OLLAMA_LLM_LIBRARY = "cpu"
    }
    else {
        Write-Host "[OLLAMA] GPU detected - using GPU acceleration" -ForegroundColor Green
        Remove-Item Env:OLLAMA_NUM_GPU -ErrorAction SilentlyContinue
        Remove-Item Env:OLLAMA_LLM_LIBRARY -ErrorAction SilentlyContinue
    }
}

# Pre-flight: stop any stale process holding port 8000 (leftover reloaders or
# crashed shells). Without this, uvicorn dies with Errno 10048 and the window
# closes silently. Note: --reload is intentionally omitted -- watchfiles watches
# backend/ and reloads on every log/data write (ollama logs, whisper cache),
# killing the server mid-startup.
$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $holderPids = $listener.OwningProcess | Sort-Object -Unique
    foreach ($pid_ in $holderPids) {
        Write-Host "[BACKEND] Stopping stale process $pid_ holding port 8000..." -ForegroundColor Yellow
        Stop-Process -Id $pid_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep 2
}

# Pre-flight: orphaned llama-server processes survive when ollama is force-killed
# (Stop-Process on ollama.exe does NOT kill its child llama-server.exe). Each leak
# holds ~400MB on the GTX 1050; after a few restarts the GPU hits cudaMalloc OOM
# and the LLM warm-up fails. Kill the whole tree before starting fresh.
$stale = Get-Process -Name "ollama","llama-server" -ErrorAction SilentlyContinue
if ($stale) {
    Write-Host "[BACKEND] Stopping $($stale.Count) stale ollama/llama-server process(es)..." -ForegroundColor Yellow
    $stale | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
}

# Start Ollama in background if not already running
$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
$ollamaExe = "D:\project\Jarvis project\Hey-Olivia\backend\ollama\ollama.exe"
$ollamaLogDir = "D:\project\Jarvis project\Hey-Olivia\backend\logs"
if (-not (Test-Path $ollamaExe)) {
    Write-Host "[OLLAMA] Not found at $ollamaExe - LLM features unavailable" -ForegroundColor Yellow
}
elseif (-not $ollamaProcess) {
    New-Item -ItemType Directory -Path $ollamaLogDir -Force | Out-Null
    Write-Host "[OLLAMA] Starting local server..." -ForegroundColor Yellow
    $null = Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden `
        -RedirectStandardOutput "$ollamaLogDir\ollama_serve.log" `
        -RedirectStandardError "$ollamaLogDir\ollama_serve_err.log"
    Start-Sleep 3
    Write-Host "[OLLAMA] Ready" -ForegroundColor Green

    if ($env:OLLAMA_LLM_LIBRARY -ne "cpu") {
        $gpuLine = Select-String -Path "$ollamaLogDir\ollama_serve_err.log" -Pattern "library=CUDA compute=" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($gpuLine) {
            Write-Host "[OLLAMA] GPU engagement confirmed: $($gpuLine.Line.Trim())" -ForegroundColor Green
        }
        else {
            Write-Host "[OLLAMA] GPU engagement not confirmed yet - check $ollamaLogDir\ollama_serve_err.log" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[OLLAMA] Already running" -ForegroundColor Green
}

$env:JARVIS_SERVICES = $Services
Set-Location "D:\project\Jarvis project\Hey-Olivia\backend"

try {
    & $backendPy -m uvicorn app.main:app --host 0.0.0.0 --port 8000
}
finally {
    Write-Host "[OLLAMA] Stopping..." -ForegroundColor Yellow
    $null = Stop-Process -Name "ollama","llama-server" -Force -ErrorAction SilentlyContinue
    Write-Host "[OLLAMA] Stopped" -ForegroundColor Green
}
