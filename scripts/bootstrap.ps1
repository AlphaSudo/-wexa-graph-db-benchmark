[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepositoryRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.11 or newer is required.'
}

if (-not (Test-Path -LiteralPath '.venv')) {
    python -m venv .venv
}

$Python = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.lock
& $Python -m pip install -e . --no-deps
& $Python -m wexa_benchmark.cli doctor --config configs/smoke.yaml --offline

Write-Host 'Bootstrap complete. No managed credentials were accessed.' -ForegroundColor Green
