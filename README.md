# CognoDB and Graph Database Benchmark

Candidate: Ahmed Yasser Morra
Status: benchmark harness implementation; no performance claim is published until correctness and audit gates pass.

This repository benchmarks CognoDB c0 against four or more graph databases using the same
MovieLens graph and logical workloads. It deliberately separates two questions:

1. **Managed-service reality:** what a developer observes from CognoDB c0 and AuraDB Free
   from the same client and region policy.
2. **Controlled engine behavior:** how Neo4j Community, Memgraph, FalkorDB, and ArangoDB
   behave when each runs alone with the same local CPU, memory, and storage limits.

Local and managed latency rows remain visible, but they are not treated as hardware-equivalent
or network-equivalent evidence.

## Quick start

Requirements: Python 3.11+, Podman or Docker with Compose, and PowerShell 7 on Windows.

```powershell
./scripts/bootstrap.ps1
./scripts/storage.ps1 setup all
.\.venv\Scripts\python.exe -m wexa_benchmark.cli prepare --config configs/smoke.yaml
.\.venv\Scripts\python.exe -m wexa_benchmark.cli doctor --config configs/smoke.yaml
```

To test one local database without touching a managed account:

```powershell
./scripts/service.ps1 start neo4j
.\.venv\Scripts\python.exe -m wexa_benchmark.cli run --config configs/smoke.yaml --target neo4j-ce-capped
./scripts/service.ps1 stop neo4j
```

After smoke validation, run all four controlled official targets in the frozen seeded order:

```powershell
./scripts/run-local-official.ps1
```

Use `configs/official.yaml` only for publishable runs. It requires 30 warm-ups, at least 100
measured read operations, three independent sessions, correctness validation, and immutable
JSONL output.

## Safety and provenance

- Secrets are read only from environment variables and are redacted from output.
- `.env` is ignored. `.env.example` contains placeholders only.
- Controlled containers bind unauthenticated ports to `127.0.0.1` only; managed targets always
  require secrets.
- Failed operations are recorded; they are never silently converted into successful samples.
- Performance publication is blocked unless dataset counts and normalized result digests pass.
- The run header includes client metadata and full target order; every raw record includes their
  stable run/order identity, config/dataset/query-bank hashes, UTC timestamp, and target ID.
- Controlled runs stream CPU, memory, I/O, and process counts every second and save exact
  filesystem/data-directory bytes.
- Official evidence can be deterministically packaged as `.jsonl.gz` without deleting local raw
  JSONL.

The complete frozen methodology is in [METHODOLOGY.md](METHODOLOGY.md), fairness decisions are
in [FAIRNESS.md](FAIRNESS.md), and exact reproduction commands are in
[REPRODUCING.md](REPRODUCING.md).

## Dataset

MovieLens `ml-latest-small` is downloaded from GroupLens and normalized locally:

- 610 `User` nodes
- 9,742 `Movie` nodes
- 100,836 directed `RATED` relationships
- 10,352 total nodes
- 610 unique user IDs, 9,742 unique movie IDs, zero duplicate rating keys, and zero broken endpoints
- 24 movies whose title has no terminal four-digit year; these are stored with `year = null`

The source archive was retrieved on 2026-08-25 at 10:51:57 UTC and is 978,202 bytes. Its SHA-256
is `696d65a3dfceac7c45750ad32df2c259311949efec81f0f144fdfb91ebc9e436`. The bundled
[MovieLens README and usage license](data/MOVIELENS_README.txt), normalized-file hashes, exact
rating/timestamp aggregates, year distribution, degree distribution, and retrieval provenance are
recorded in [data/manifest.json](data/manifest.json).

The fixed official query bank contains 100 degree-stratified starts (25 per rank bucket) and has
SHA-256 `9d15309a4802f5d956918c523e93be8460c3e7d483d0cd6f9be89a9227e7ccbc`.
Raw and normalized rows are regenerated rather than committed.

## Results

The controlled-local official run is complete for ArangoDB, FalkorDB, Memgraph, and Neo4j
Community. See the generated [official benchmark summary](results/generated/official-summary.md)
for ingest, read latency, degree-stratified traversal, mixed workload, open-loop saturation,
resource, query-plan, and connection-baseline results. Compressed raw ledgers and post-run
container evidence are committed alongside it.

CognoDB c0 and Neo4j Aura remain explicitly marked `missing` until fresh credentials and the
exact Aura tier are supplied. No values are estimated or copied into missing cells.
