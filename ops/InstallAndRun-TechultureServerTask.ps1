param()

$ErrorActionPreference = "Stop"

$taskName = "TechultureServer"
$projectRoot = Split-Path -Parent $PSScriptRoot
$hiddenScriptPath = Join-Path $PSScriptRoot "run_techulture_server_hidden.vbs"

if (-not (Test-Path $hiddenScriptPath)) {
    throw "Cannot find hidden server runner script: $hiddenScriptPath"
}

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$hiddenScriptPath`"" -WorkingDirectory $projectRoot
$startupTrigger = New-ScheduledTaskTrigger -AtStartup
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn
$triggers = @($startupTrigger, $logonTrigger)
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([timespan]::Zero) `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 10 `
    -Hidden

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Description "Techulture local web server" `
    -Force | Out-Null

Start-ScheduledTask -TaskName $taskName
Write-Host "Triggered immediate run for '$taskName'."

$info = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host "Task '$taskName' installed."
Write-Host "Mode: SilentVbs"
Write-Host "Target URL: http://127.0.0.1:8021/"
Write-Host "Next run: $($info.NextRunTime)"
Write-Host "Last run: $($info.LastRunTime)"
