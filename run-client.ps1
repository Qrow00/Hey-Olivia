Write-Host "Starting J.A.R.V.I.S. Client..." -ForegroundColor Cyan
Set-Location "D:\project\Jarvis project\Hey-Olivia\client"
$env:PATH = "C:\flutter\bin;C:\Program Files\Git\cmd;$env:PATH"
flutter run -d windows
