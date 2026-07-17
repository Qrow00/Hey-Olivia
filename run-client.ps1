Write-Host "Starting J.A.R.V.I.S. Client..." -ForegroundColor Cyan
Set-Location "C:\Users\toshi\Documents\main jarvis\client"
$env:PATH = "C:\flutter\bin;$env:PATH"
flutter run -d windows
