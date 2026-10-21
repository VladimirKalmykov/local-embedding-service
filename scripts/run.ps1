[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw 'Service environment is missing. Run scripts\setup.ps1 first.'
}

if (-not $env:LOCAL_EMBEDDING_MODEL_CACHE) {
    $env:LOCAL_EMBEDDING_MODEL_CACHE = Join-Path $RepoRoot '.models'
}

& $VenvPython -m local_embedding_service

