# Reproducing the Benchmark

## 1. Install and prepare

```powershell
git clone https://github.com/AlphaSudo/-wexa-graph-db-benchmark.git
cd -wexa-graph-db-benchmark
./scripts/bootstrap.ps1
.\.venv\Scripts\python.exe -m wexa_benchmark.cli prepare --config configs/official.yaml
```

## 2. Configure credentials

Copy `.env.example` to `.env`, replace only the targets you intend to run, and keep that file
local. The runner reads `.env` without printing its values. Managed connection URIs and passwords
must never be passed on the command line because shell history is evidence too.

## 3. Run controlled local targets

Run only one engine at a time:

```powershell
./scripts/storage.ps1 setup all
./scripts/run-local-official.ps1
```

The orchestrator follows the seeded order in `configs/official.yaml`. To run one target manually:

```powershell
./scripts/service.ps1 start neo4j
.\.venv\Scripts\python.exe -m wexa_benchmark.cli run --config configs/official.yaml --target neo4j-ce-capped
./scripts/service.ps1 evidence neo4j postrun
./scripts/service.ps1 stop neo4j
```

Repeat with `memgraph`, `falkordb`, and `arangodb`. Evidence is saved separately from benchmark
samples. Never start multiple local services for an official run.

## 4. Run managed targets

```powershell
.\.venv\Scripts\python.exe -m wexa_benchmark.cli run --config configs/official.yaml --target cognodb-c0
.\.venv\Scripts\python.exe -m wexa_benchmark.cli run --config configs/official.yaml --target neo4j-aura-free
```

## 5. Audit

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m wexa_benchmark.cli audit --config configs/official.yaml
.\.venv\Scripts\python.exe -m wexa_benchmark.cli package --config configs/official.yaml
```

The audit is intentionally strict: incomplete metric cells, validation failures, checksum
changes, placeholders, and secret-like output make the command fail.
The package command creates deterministic, commit-ready `.jsonl.gz` copies and never deletes the
local append-only `.jsonl` source.
