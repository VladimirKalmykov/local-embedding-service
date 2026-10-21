[CmdletBinding()]
param(
    [string]$TaskName = 'Local Embedding Service'
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$RunScript = Join-Path $RepoRoot 'scripts\run.ps1'
$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw 'Service environment is missing. Run scripts\setup.ps1 first.'
}

$WindowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$Identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$ActionArguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $RunScript
$Action = New-ScheduledTaskAction `
    -Execute $WindowsPowerShell `
    -Argument $ActionArguments `
    -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $Identity
$Principal = New-ScheduledTaskPrincipal `
    -UserId $Identity `
    -LogonType Interactive `
    -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description 'Starts the per-user Local Embedding Service on Windows logon.' `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

$Deadline = [DateTime]::UtcNow.AddSeconds(20)
do {
    try {
        $Health = Invoke-RestMethod -Uri 'http://127.0.0.1:7342/health' -TimeoutSec 2
        if ($Health.status -eq 'ready') {
            Write-Host "Autostart installed and service is healthy: $TaskName"
            exit 0
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
} while ([DateTime]::UtcNow -lt $Deadline)

$Task = Get-ScheduledTask -TaskName $TaskName
$TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
throw "Task was registered but the service did not become healthy. State=$($Task.State), LastTaskResult=$($TaskInfo.LastTaskResult)"
