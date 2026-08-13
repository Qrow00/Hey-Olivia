<#>
.SYNOPSIS
    Launch J.A.R.V.I.S. V3 Thermal Logger
.DESCRIPTION
    Starts the thermal diagnostic logger for ASUS GL553VD shutdown diagnosis.
    Requires OpenHardwareMonitor running for GPU temp data.
.NOTES
    Logs to data/logs/thermal_diag_YYYYMMDD.tsv
#>

param(
    [int]$Interval = 30,
    [string]$LogDir = "data\logs"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. V3 - Thermal Logger" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Interval: $Interval seconds" -ForegroundColor Green
Write-Host "Log Dir: $LogDir" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

# Check if OpenHardwareMonitor is running
$ohm = Get-Process -Name "OpenHardwareMonitor" -ErrorAction SilentlyContinue
if ($ohm) {
    Write-Host "OpenHardwareMonitor detected - GPU temps available" -ForegroundColor Green
} else {
    Write-Warning "OpenHardwareMonitor not running - GPU temps unavailable"
    Write-Warning "Download from: https://openhardwaremonitor.org/"
}

# Set working directory
Set-Location "$PWD\backend_new"

# Start thermal logger
try {
    python -c "
import asyncio
import sys
sys.path.insert(0, '.')
os.chdir('.')

from app.plugins.thermal import ThermalLoggerPlugin

async def main():
    plugin = ThermalLoggerPlugin()
    # Mock kernel
    class MockKernel: pass
    await plugin.start(MockKernel())
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await plugin.stop(MockKernel())

import asyncio
asyncio.run(main())
"
}
catch {
    Write-Error "Failed to start thermal logger: $_"
    Read-Host "Press Enter to exit"
}