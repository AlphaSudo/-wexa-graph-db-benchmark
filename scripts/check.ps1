[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Run scripts/bootstrap.ps1 first.'
}

Set-Location -LiteralPath $RepositoryRoot
& $Python -m ruff format --check .
& $Python -m ruff check .
& $Python -m pyright --pythonpath $Python
& $Python -m pytest
& $Python -m compileall -q src tests

Write-Host 'Formatting, lint, types, tests, and bytecode compilation passed.' -ForegroundColor Green
