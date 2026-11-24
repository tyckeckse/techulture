param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $projectRoot "logs"
$null = New-Item -ItemType Directory -Path $logDir -Force

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logPath = Join-Path $logDir "techulture_refresh_$timestamp.log"

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $venvPythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPythonExe) {
        $resolvedPythonExe = (Resolve-Path -LiteralPath $venvPythonExe).Path
    }
    else {
        $resolvedPythonExe = "py"
    }
}
else {
    $isPathLike = $PythonExe.Contains("\") -or $PythonExe.Contains("/")
    if ($isPathLike) {
        $candidatePythonExe = $PythonExe
        if (-not [System.IO.Path]::IsPathRooted($candidatePythonExe)) {
            $candidatePythonExe = Join-Path $projectRoot $candidatePythonExe
        }
        if (-not (Test-Path -LiteralPath $candidatePythonExe)) {
            throw "Python executable not found: $candidatePythonExe"
        }
        $resolvedPythonExe = (Resolve-Path -LiteralPath $candidatePythonExe).Path
    }
    else {
        $resolvedPythonExe = $PythonExe
    }
}

Push-Location $projectRoot
try {
    Write-Host "Running Techulture refresh at $(Get-Date -Format s)"

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
            $previousNativePreference = $PSNativeCommandUseErrorActionPreference
            $PSNativeCommandUseErrorActionPreference = $false
        }

        & $resolvedPythonExe "techulture.py" `
            --store ".\data\store.json" `
            --out ".\index.html" 2>&1 | Tee-Object -FilePath $logPath
    }
    finally {
        if (Get-Variable -Name previousNativePreference -ErrorAction SilentlyContinue) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePreference
        }
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($LASTEXITCODE -ne 0) {
        throw "techulture.py failed with exit code $LASTEXITCODE"
    }

    Write-Host "Done. Log: $logPath"
}
catch {
    $_ | Out-File -FilePath $logPath -Append
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}
