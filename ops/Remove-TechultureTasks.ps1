param()

$ErrorActionPreference = "Stop"

$refreshRemover = Join-Path $PSScriptRoot "Remove-TechultureRefreshTask.ps1"
$serverRemover = Join-Path $PSScriptRoot "Remove-TechultureServerTask.ps1"

if (-not (Test-Path $refreshRemover)) {
    throw "Cannot find refresh task remover: $refreshRemover"
}

if (-not (Test-Path $serverRemover)) {
    throw "Cannot find server task remover: $serverRemover"
}

Write-Host "Removing refresh task..."
& $refreshRemover

Write-Host "Removing server task..."
& $serverRemover

Write-Host "All Techulture tasks are removed."
