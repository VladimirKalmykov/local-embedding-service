[CmdletBinding()]
param(
    [string]$TaskName = 'Local Embedding Service'
)

$ErrorActionPreference = 'Stop'
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $Task) {
    Write-Host "Autostart task is not installed: $TaskName"
    exit 0
}

if ($Task.State -eq 'Running') {
    Stop-ScheduledTask -TaskName $TaskName
}
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Autostart task removed: $TaskName"
