Write-Host "Starting J.A.R.V.I.S. Backend (voice-only mode)..." -ForegroundColor Green
$env:JARVIS_SERVICES = "api"
Set-Location "D:\project\Jarvis project\Hey-Olivia\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Write-Host ""
Write-Host "Voice pipeline uses deferred loading — Whisper model loads on first STT request." -ForegroundColor Gray
