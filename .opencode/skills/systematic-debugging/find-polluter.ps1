# Bisection script to find which test creates unwanted files/state
# Usage: find-polluter.ps1 <file_or_dir_to_check> <test_command_prefix>
# Example: find-polluter.ps1 '.git' "npm test -- src"
#
# On this Windows machine the opencode shell runs with a Restricted execution
# policy, so invoke via:
#   powershell -NoProfile -ExecutionPolicy Bypass -File find-polluter.ps1 <args>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PollutionCheck,
    [Parameter(Mandatory = $true)]
    [string]$TestCommand
)

$ErrorActionPreference = "Stop"

Write-Output "Searching for test that creates: $PollutionCheck"
Write-Output "Test command: $TestCommand"
Write-Output ""

$testFiles = @(Get-ChildItem -Recurse -File -Include *.test.ts,*.test.tsx,*.test.js,*.test.jsx,*.test.py,*.test.mjs -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
$testFiles = @($testFiles | Where-Object { $_ -notmatch "node_modules|\.git|\.venv|venv" } | Sort-Object -Unique)

if ($testFiles.Count -eq 0) {
    Write-Output "No test files found matching *.test.{ts,tsx,js,jsx,py,mjs}"
    exit 0
}

Write-Output "Found $($testFiles.Count) test files"
Write-Output ""

$count = 0
foreach ($testFile in $testFiles) {
    $count++

    if (Test-Path $PollutionCheck) {
        Write-Output "⚠️  Pollution already exists before test $count/$($testFiles.Count)"
        Write-Output "   Skipping: $testFile"
        continue
    }

    Write-Output "[$count/$($testFiles.Count)] Testing: $testFile"

    & cmd /c "$TestCommand `"$testFile`" 2>&1" | Out-Null

    if (Test-Path $PollutionCheck) {
        Write-Output ""
        Write-Output "🏁 FOUND POLLUTER!"
        Write-Output "   Test: $testFile"
        Write-Output "   Created: $PollutionCheck"
        Write-Output ""
        Write-Output "Pollution details:"
        Get-ChildItem $PollutionCheck | Format-List FullName, LastWriteTime, Length
        Write-Output ""
        Write-Output "To investigate:"
        Write-Output "  $TestCommand `"$testFile`"    # Run just this test"
        Write-Output "  Get-Content `"$testFile`"     # Review test code"
        exit 1
    }
}

Write-Output ""
Write-Output "✅ No polluter found - all tests clean!"
exit 0
