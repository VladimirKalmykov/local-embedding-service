[CmdletBinding()]
param(
    [string]$TaskName = 'Local Embedding Service'
)

$ErrorActionPreference = 'Stop'
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $Task) {
    [pscustomobject]@{
        Installed = $false
        TaskName = $TaskName
        TaskState = $null
        ServiceHealthy = $false
    }
    exit 1
}

$TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
$Healthy = $false
try {
    $Health = Invoke-RestMethod -Uri 'http://127.0.0.1:7342/health' -TimeoutSec 2
    $Healthy = $Health.status -eq 'ready'
} catch {
    $Healthy = $false
}

[pscustomobject]@{
    Installed = $true
    TaskName = $TaskName
    TaskState = [string]$Task.State
    LastTaskResult = $TaskInfo.LastTaskResult
    ServiceHealthy = $Healthy
}

if (-not $Healthy) {
    exit 1
}
