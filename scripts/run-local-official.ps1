[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'
$Config = 'configs/official.yaml'
$Targets = @(
    [pscustomobject]@{ Service = 'arangodb'; Target = 'arangodb-capped' },
    [pscustomobject]@{ Service = 'falkordb'; Target = 'falkordb-capped' },
    [pscustomobject]@{ Service = 'memgraph'; Target = 'memgraph-capped' },
    [pscustomobject]@{ Service = 'neo4j'; Target = 'neo4j-ce-capped' }
)

if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Run scripts/bootstrap.ps1 before the official benchmark.'
}

Push-Location $RepositoryRoot
try {
    & (Join-Path $PSScriptRoot 'storage.ps1') setup all
    foreach ($Entry in $Targets) {
        Write-Host "Starting official target $($Entry.Target)"
        & (Join-Path $PSScriptRoot 'service.ps1') start $Entry.Service
        try {
            & $Python -m wexa_benchmark.cli run --config $Config --target $Entry.Target
            if ($LASTEXITCODE -ne 0) {
                throw "Official run failed for $($Entry.Target); raw evidence was preserved."
            }
            & (Join-Path $PSScriptRoot 'service.ps1') evidence $Entry.Service postrun
        }
        finally {
            & (Join-Path $PSScriptRoot 'service.ps1') stop $Entry.Service
        }
    }
}
finally {
    Pop-Location
}
