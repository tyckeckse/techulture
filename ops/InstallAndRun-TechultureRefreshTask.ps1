param(
    [string]$TaskName = "TechultureRefresh"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$hiddenScriptPath = Join-Path $PSScriptRoot "run_techulture_refresh_hidden.vbs"

if (-not (Test-Path $hiddenScriptPath)) {
    throw "Cannot find hidden runner script: $hiddenScriptPath"
}

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$hiddenScriptPath`"" -WorkingDirectory $projectRoot
$hourlyTrigger = New-ScheduledTaskTrigger -Once -At "00:00" `
    -RepetitionInterval (New-TimeSpan -Hours 1)
$startupTrigger = New-ScheduledTaskTrigger -AtStartup
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn
$triggers = @($hourlyTrigger, $startupTrigger, $logonTrigger)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -Hidden

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Description "Techulture scheduled refresh" `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Write-Host "Triggered immediate run for '$TaskName'."

$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Task '$TaskName' installed."
Write-Host "Mode: SilentVbs"
Write-Host "Schedule: Hourly"
Write-Host "Next run: $($info.NextRunTime)"
Write-Host "Last run: $($info.LastRunTime)"
