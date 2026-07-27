Write-Host "Starting J.A.R.V.I.S. Backend..." -ForegroundColor Cyan
Set-Location "D:\project\Jarvis project\Hey-Olivia\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
