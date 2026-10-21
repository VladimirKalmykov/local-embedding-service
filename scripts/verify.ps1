[CmdletBinding()]
param(
    [switch]$SkipModel
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw 'Service environment is missing. Run scripts\setup.ps1 first.'
}

$env:LOCAL_EMBEDDING_MODEL_CACHE = Join-Path $RepoRoot '.models'
$VerifyArgs = @('-m', 'local_embedding_service.verification')
if ($SkipModel) {
    $VerifyArgs += '--skip-model'
}
& $VenvPython @VerifyArgs
if ($LASTEXITCODE -ne 0) {
    throw 'Runtime verification failed.'
}

