param(
    [float]$Interval = 5
)

$root = "D:\project\Jarvis project\Hey-Olivia"
$script = Join-Path $root "backend\tools\thermal_diag_logger.py"
Start-Process python -ArgumentList "`"$script`" --interval $Interval" -WorkingDirectory $root
Write-Host "[THERMAL] logger started in its own window (interval ${Interval}s). Logs go to $root\data\logs\" -ForegroundColor Cyan
