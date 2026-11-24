param()

$ErrorActionPreference = "Stop"

$refreshInstaller = Join-Path $PSScriptRoot "InstallAndRun-TechultureRefreshTask.ps1"
$serverInstaller = Join-Path $PSScriptRoot "InstallAndRun-TechultureServerTask.ps1"

if (-not (Test-Path $refreshInstaller)) {
    throw "Cannot find refresh task installer: $refreshInstaller"
}

if (-not (Test-Path $serverInstaller)) {
    throw "Cannot find server task installer: $serverInstaller"
}

Write-Host "Installing refresh task..."
& $refreshInstaller

Write-Host "Installing server task..."
& $serverInstaller

Write-Host "All Techulture tasks are installed and triggered."
