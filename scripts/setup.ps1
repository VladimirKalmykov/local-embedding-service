[CmdletBinding()]
param(
    [switch]$SkipModelCheck
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$VenvPath = Join-Path $RepoRoot '.venv'
$VenvPython = Join-Path $VenvPath 'Scripts\python.exe'
$ModelCache = Join-Path $RepoRoot '.models'
$LockPath = Join-Path $RepoRoot 'requirements\service.lock.txt'

$SystemPython = (Get-Command python -ErrorAction Stop).Source
$PythonVersion = & $SystemPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($PythonVersion -ne '3.12') {
    throw "Local Embedding Service requires Python 3.12; found $PythonVersion at $SystemPython"
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    & $SystemPython -m venv $VenvPath
}

& $VenvPython -m pip install --disable-pip-version-check --requirement $LockPath
if ($LASTEXITCODE -ne 0) {
    throw 'Locked dependency installation failed.'
}

& $VenvPython -m pip install --disable-pip-version-check --no-deps --editable $RepoRoot
if ($LASTEXITCODE -ne 0) {
    throw 'Editable service installation failed.'
}

New-Item -ItemType Directory -Force $ModelCache | Out-Null
$env:LOCAL_EMBEDDING_MODEL_CACHE = $ModelCache

& $VenvPython -m unittest discover -s (Join-Path $RepoRoot 'tests') -v
if ($LASTEXITCODE -ne 0) {
    throw 'Unit tests failed.'
}

$VerifyArgs = @('-m', 'local_embedding_service.verification')
if ($SkipModelCheck) {
    $VerifyArgs += '--skip-model'
}
& $VenvPython @VerifyArgs
if ($LASTEXITCODE -ne 0) {
    throw 'Runtime verification failed.'
}

Write-Host ''
Write-Host 'Local Embedding Service setup completed.'
Write-Host "Python: $VenvPython"
Write-Host "Model cache: $ModelCache"
Write-Host "Run: .\scripts\run.ps1"

