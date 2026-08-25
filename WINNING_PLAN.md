# Wexa Graph Database Benchmark - Winning Plan

Status: implementation-ready, updated from live account and local-machine evidence on 2026-08-25

Candidate: Ahmed Yasser Morra
Assessment received: 2026-08-24 10:03 Africa/Cairo
Assumed 48-hour deadline: 2026-08-26 10:03 Africa/Cairo
GitHub: `AlphaSudo`; public repository created at `AlphaSudo/-wexa-graph-db-benchmark` (rename recommended)
Cloud budget: zero; official work will use managed free tiers plus locally capped containers

## 1. Mission and source hierarchy

The goal is not to manufacture a CognoDB victory. The goal is to deliver a benchmark that a database engineer can audit, a reviewer can reproduce, and a broad technical audience can understand.

Source hierarchy for this plan:

1. The five-page Wexa assessment PDF is the binding specification.
2. `wexaassignment.txt` is advisory material. Its ideas were selected, modified, or rejected according to the assessment, time risk, and current product facts.
3. Current official vendor documentation is used only to verify facts that can change, such as free-tier limits, regions, and supported deployment methods.
4. Benchmark results will come only from our own captured runs. No suggested, vendor-published, extrapolated, or placeholder number may enter the results matrix.

## 2. The score-winning thesis

The submission will make misleading conclusions difficult to publish, including our own. Five mechanisms carry that thesis:

1. A visible fairness dossier that separates managed-service reality from resource-controlled engine behavior.
2. A correctness gate that blocks performance publication until data and query semantics match.
3. A deterministic, degree-stratified query bank instead of accidental easy-node sampling.
4. A seeded, persisted one-at-a-time target order with repeated sessions, tails, confidence,
   failures, and offered-versus-achieved load.
5. An automatically generated report and article in which every claim is labeled as observation, evidence, explanation, confidence, and confirmation needed.

This directly targets the rubric:

| Criterion | Weight | How we earn it |
|---|---:|---|
| Methodology and fairness | 25% | Day-zero spec capture, two comparison lenses, same dataset/query bank/client/region, strict container caps, pre-registered policy, honest deviation ledger |
| Completeness of metrics | 20% | Machine-audited target-by-metric matrix; ingest, all reads, aggregation, mixed throughput, and footprint for every target; failures remain visible |
| Reproducibility and code quality | 20% | Typed adapter architecture, pinned dependencies and images, one-command workflows, immutable raw results, CI static/unit gate, clean-clone rehearsal |
| README and analysis | 15% | One-screen summary, full matrix, generated charts, evidence-backed root-cause analysis, limitations, decision guide |
| Communication | 20% | Article-quality README, standalone public article, short demo, public peer-review launch, honest engagement receipts |

## 3. Decisions already made

### 3.1 Dataset: MovieLens `ml-latest-small`

Use only these two node types and one relationship type:

- `(:User {userId})`: 610 nodes
- `(:Movie {movieId, title, year, genres})`: 9,742 nodes
- `(:User)-[:RATED {rating, timestamp}]->(:Movie)`: 100,836 relationships

Expected primary graph size: 10,352 nodes and 100,836 relationships.

Why this is the best 48-hour choice:

- It is public, familiar, easy to explain, and already clears the 100,000-relationship requirement without arbitrary graph sampling.
- It fits the current AuraDB Free documented cap of 50,000 nodes and 175,000 relationships.
- It has real properties for point lookup, indexed filtering, and aggregation.
- Its bipartite structure produces meaningful 1-hop, 2-hop, and 3-hop fan-out behavior.
- The exact archive, extracted files, normalized files, and graph manifest will all receive SHA-256 checksums.

Primary source: [GroupLens MovieLens small README](https://files.grouplens.org/datasets/movielens/ml-latest-small-README.html).

### 3.2 Deployment targets

We will benchmark six deployment targets representing CognoDB plus four distinct competitors: Neo4j, Memgraph, FalkorDB, and ArangoDB.

| Target ID | Deployment | Role | Interface | Resource treatment |
|---|---|---|---|---|
| `cognodb-c0` | CognoDB Cloud c0 | Required subject | Bolt + Cypher, official Neo4j driver | Live console allocation defines `B = 512 MiB` |
| `neo4j-aura-free` | Neo4j AuraDB Free | Managed-service peer | Bolt + Cypher, official Neo4j driver | Hardware is opaque; compare only as entry-tier product reality |
| `neo4j-ce-capped` | Neo4j Community container | Controlled Neo4j baseline | Bolt + Cypher | 0.5 vCPU, `B` memory, no swap, 1 GiB data filesystem |
| `memgraph-capped` | Memgraph Community container | In-memory/C++ contrast | Bolt + Cypher | Same strict cap |
| `falkordb-capped` | FalkorDB server container | Redis/sparse-matrix contrast | Redis protocol + Cypher | Same strict cap |
| `arangodb-capped` | ArangoDB Community container | Multi-model/AQL contrast | HTTP + AQL | Same strict cap plus Arango's documented resource-detection overrides |

This is deliberately six targets, not nine. It gives us:

- A managed lens: CognoDB c0 versus AuraDB Free.
- A resource-controlled lens: four self-hosted competitor engines on one identical host, one at a time, with identical cgroup and disk limits.
- A Neo4j deployment control: AuraDB versus capped Neo4j Community helps expose managed/network/tier effects without pretending they are pure engine effects.
- A complete master matrix across all targets, with comparison claims limited to the lens that can support them.

Official setup references:

- [CognoDB developers and regions](https://cognodb.com/developers)
- [CognoDB pricing](https://cognodb.com/pricing)
- [AuraDB Free current limits](https://neo4j.com/free-graph-database/)
- [AuraDB Free regions and ports](https://neo4j.com/docs/aura/security/ip-addresses/)
- [Neo4j Docker](https://www.neo4j.com/docs/operations-manual/current/docker/introduction/)
- [Memgraph Docker](https://memgraph.com/docs/getting-started/install-memgraph/docker)
- [FalkorDB Docker](https://docs.falkordb.com/operations/docker)
- [ArangoDB Docker and resource overrides](https://docs.arango.ai/arangodb/3.12/operations/installation/docker/)

### 3.3 Day-zero resource gate: resolved at 512 MiB

The assessment says CognoDB c0 has 256 MB RAM. The candidate's live CognoDB console on 2026-08-25 shows c0 with 512 MB RAM, burst to 0.5 vCPU, 1 GiB storage, up to 500 IOPS, 200 maximum connections, engine v0.9.11, and a 50,000-row result cap. The live allocation therefore freezes `B = 512 MiB` for the primary local parity runs.

Before code or data is optimized for a winner:

1. Preserve the assessment's 256 MB statement.
2. Preserve a dated sanitized record of the live 512 MB console specification without endpoint or credentials.
3. Cap every self-hosted target to 0.5 vCPU, 512 MiB memory, no swap, and a 1 GiB data filesystem.
4. Add one optional 256 MiB self-hosted sensitivity run only after required results are complete.
5. Record the discrepancy and its likely direction of bias in `FAIRNESS.md`; do not silently choose the more convenient number.

AuraDB Free remains a managed-entry-tier comparison because exact CPU/RAM is not exposed. It must never be described as hardware-parity evidence.

### 3.4 Region and test topology

Use the existing zero-cost CognoDB c0 in `us-east4` and disclose its region. Confirm the Neo4j
target is AuraDB Free and record its actual region. The managed lens is developer-observed entry-tier
reality, not a claim of network, region, or hidden-hardware parity. Rotate both exposed credentials.

Zero-budget topology:

- The benchmark client runs on the candidate's Windows 11 Pro PC for every target.
- Local hardware: Intel Core i7-1065G7, 4 cores/8 logical processors, 7.8 GiB host RAM, and more than 120 GiB free disk at preflight.
- Self-hosted targets run one at a time through Podman 5.7.1 on WSL2/cgroup v2.
- Managed CognoDB and AuraDB Free are reached from the same Cairo client; their actual regions are
  recorded and any difference remains a headline caveat.
- Runtime, driver versions, connection-pool policy, timeouts, workload schedule, and query bank remain identical for every target.

This produces two defensible lenses, not one falsely uniform table:

- Managed lens: CognoDB c0 versus confirmed AuraDB Free, same remote region and same Cairo client.
- Controlled local lens: Neo4j CE, Memgraph, FalkorDB, and ArangoDB, one at a time on the same Podman host with identical caps.

Local engines have a major network advantage over managed services. Cross-lens numbers remain in the master matrix because the assessment asks for them, but the report will not call a local-versus-remote latency difference an engine result. TCP/TLS/fresh-connection time and warm `RETURN 1` latency will be reported beside query latency. We will not subtract RTT and call the remainder "database time."

For storage parity, each capped engine receives its own 1 GiB data filesystem/volume mounted at the engine data directory. Before official runs, a preflight must prove Podman enforces 0.5 CPU and 512 MiB memory; the current environment exposes cgroup v2 memory controls, while CPU quota still needs an empirical verification. Evidence includes filesystem capacity, `du`, image digest, container inspect output, and in-container cgroup values.

### 3.5 Implementation stack

Use the available Python 3.11 runtime, pinned packages, and a typed package.

Why Python rather than JMH/Java for this assessment:

- The benchmark is remote I/O and workload orchestration, not a JVM microbenchmark.
- Python has mature official/client libraries for all selected targets and a fast path to asynchronous load generation, statistics, and charting.
- A single language can own adapters, raw-result schemas, analysis, and report generation inside the 48-hour limit.
- Type hints, dataclasses/Pydantic models, Ruff, Pyright, and tests will keep it reviewable for a Java-oriented engineer.

Timing uses `time.perf_counter_ns()`. Raw samples are retained; Markdown numbers are never hand-entered.

## 4. Benchmark contract

### 4.1 Pre-registration

Before the first official run, commit `METHODOLOGY.md` and `configs/official.yaml` containing:

- target list and versions
- dataset checksums and expected counts
- graph schema and index policy
- exact logical query contract and per-engine translation
- seed (`20260825`)
- fixed query bank IDs and degree buckets
- warm-up and measured iteration counts
- timeout, retry, and exclusion rules
- batch size and load order
- mixed workload mixes, concurrency levels, durations, and arrival model
- statistical summaries and chart definitions
- fairness deviations known before results

Any later methodology change requires a dated decision record explaining why and whether prior runs were invalidated.

### 4.2 Schema and index policy

Equivalent logical indexes:

- unique/indexed `User.userId`
- unique/indexed `Movie.movieId`
- secondary index on `Movie.year`

The report states the actual DDL and whether the execution plan shows index use on each platform. Index/constraint creation time is reported separately.

### 4.3 Correctness gate

No performance row can become publishable until its target passes:

- exact node and relationship counts
- unique ID counts for both labels/types
- no unexpected duplicate `RATED` edge keys
- deterministic source-property totals
- 100 sampled degree checks
- selected adjacency-list SHA-256 digests
- normalized result cardinality and digest for every read workload
- equivalent write effect followed by rollback/reset validation
- directedness, `DISTINCT`, path-length, null, and aggregation semantics review

The runner state machine is:

`PROVISIONED -> LOADED -> VALIDATED -> BENCHMARKED -> REPORTED`

`VALIDATION_FAILED` blocks benchmark publication. The failure and diagnostic remain in the run ledger.

### 4.4 Deterministic degree-stratified query bank

Build the query bank once from source data using seed `20260825`, sampling without replacement inside each bucket:

- low degree: bottom 25%
- medium degree: 25th-75th percentile
- high degree: 75th-95th percentile
- hubs: top 5%
- 25 users per bucket, 100 fixed traversal starts total

The primary headline reports all starts together; the analysis also reports each bucket. This still satisfies the assessment's random-start intent while preventing a random draw from accidentally favoring low-degree nodes.

### 4.5 Logical workloads

All query translations must return the same logical scalar/result set.

| Workload | Logical operation | Required reporting |
|---|---|---|
| Ingest nodes | Empty-reset, batched `CREATE` user/movie load | nodes/s, wall time |
| Ingest relationships | Empty-reset, batched `CREATE` rating load | relationships/s, wall time |
| End-to-ready ingest | Reset through indexes and correctness counts | total wall time plus phase breakdown |
| 1-hop | User to rated movies | p50/p95 plus p99, failures, degree bucket |
| 2-hop | User to distinct peer users through a movie | same |
| 3-hop | User to distinct movies through peer users | same |
| Point lookup | Movie by indexed `movieId` | same |
| Filtered lookup | Movies by indexed `year` | same plus plan/index evidence |
| Aggregation | Rating value grouped and counted | same; full result consumed |
| Mixed write | Idempotent update of a preselected node benchmark property | throughput/latency/errors; no graph growth |
| Footprint | Stored size, memory and CPU where observable | observed value or explicit `not observable` |

The primary ingest comparison uses one common driver-batching policy and batch size. Native bulk import, if time remains, is an appendix called "best available path" and never replaces the common-path headline.

### 4.6 Repetition, warm-up, order, and failures

- 30 unmeasured warm-up operations per read workload per target.
- At least 100 measured operations per read workload per independent session.
- Three independent sessions for each official workload.
- Platform order is seeded and randomized for every short measurement round.
- UTC start/end, target order, client CPU/RAM, RTT baseline, pool wait, retries, reconnects, timeouts, and errors are recorded.
- A timeout is not a very slow success. It is reported as a failure and is not silently removed.
- Percentiles use successful observations and always appear beside success count, timeout rate, and error rate.
- If success rate is below 95%, the headline is the reliability failure, not the successful-query percentile.

### 4.7 Mixed workload and coordinated omission

Closed-loop saturation sweep:

- concurrency: 1, 5, 10, 20, 40
- duration: 60 seconds per level
- mixes: read-heavy 95/5 and mixed 80/20
- read selection: point lookup, 1-hop, and 2-hop from the fixed bank
- write selection: steady-state idempotent property update
- report offered operations where meaningful, achieved QPS, p50/p95/p99, errors, timeouts, retries, completed reads, and completed writes

Open-loop test:

- one 80/20 run at 100 scheduled requests/second for 60 seconds
- record latency from intended send time so queuing remains visible
- report offered versus achieved throughput
- if the pilot proves 100 requests/second invalid for every target, preserve that pilot and pre-register one lower common rate before official runs

### 4.8 Statistical output

Required: p50 and p95.

Additional: p99, min/max, median absolute deviation or coefficient of variation, valid sample count, error/timeout/retry rate, and bootstrap 95% confidence intervals across repeated sessions.

Language rules for conclusions:

- Do not say "fastest" when confidence intervals overlap materially.
- Do not infer server execution time by subtracting network latency.
- Distinguish observation from explanation.
- Do not assert an optimizer, storage, locking, caching, or throttling cause without plan/telemetry evidence.
- Use `not observable` rather than estimating hidden managed metrics.

## 5. Harness architecture

Planned repository:

```text
wexa-graph-db-benchmark/
|-- README.md
|-- ARTICLE.md
|-- METHODOLOGY.md
|-- FAIRNESS.md
|-- LIMITATIONS.md
|-- REPRODUCING.md
|-- CONTRIBUTING.md
|-- LICENSE
|-- Makefile
|-- pyproject.toml
|-- uv.lock
|-- .env.example
|-- .gitignore
|-- .github/workflows/ci.yml
|-- configs/
|   |-- official.yaml
|   `-- smoke.yaml
|-- data/
|   |-- README.md
|   |-- manifest.json
|   `-- checksums.sha256
|-- workloads/
|   |-- canonical.yaml
|   `-- query_bank.json
|-- infra/
|   |-- terraform/
|   |-- docker-compose.parity.yml
|   `-- storage-quota/
|-- src/graphbench/
|   |-- cli.py
|   |-- models.py
|   |-- adapters/
|   |-- dataset/
|   |-- validation/
|   |-- workloads/
|   |-- orchestration/
|   |-- statistics/
|   `-- reporting/
|-- tests/
|-- results/
|   |-- raw/
|   |-- processed/
|   |-- charts/
|   `-- manifest.json
`-- docs/
    |-- QUERY_CONTRACT.md
    |-- DECISIONS.md
    |-- CAVEATS_LEDGER.md
    `-- INTERVIEW_DEFENSE.md
```

Core commands:

```text
./scripts/check.ps1
.\.venv\Scripts\python.exe -m wexa_benchmark.cli prepare --config configs/official.yaml
./scripts/run-local-official.ps1
.\.venv\Scripts\python.exe -m wexa_benchmark.cli report --config configs/official.yaml
.\.venv\Scripts\python.exe -m wexa_benchmark.cli audit --config configs/official.yaml
.\.venv\Scripts\python.exe -m wexa_benchmark.cli package --config configs/official.yaml
```

The adapter contract covers connection, reset, schema/index creation, batched node/relationship load, logical workload execution, footprint collection, and explain/profile capture. Target-specific code translates semantics; common code owns timing, scheduling, retries, result normalization, statistics, and artifact writing.

Raw JSONL is append-only and schema-versioned. Every record includes run ID, timestamp, git SHA, config hash, dataset hash, query-bank hash, target/version/image digest, client metadata, attempt number, latency, result digest, and error classification.

The automated audit fails if any expected target/read-session/mixed/resource/plan cell is absent,
if correctness/provenance is stale, or if a likely secret appears in a raw artifact.

## 6. Deadline recovery plan

At 2026-08-25 13:27 Cairo time, the conservative 48-hour interpretation leaves approximately 20 hours 35 minutes. The original 48-hour schedule is superseded by this finish-first schedule:

| Cairo time | Work | Exit evidence |
|---|---|---|
| 13:30-14:15 | Rotate managed credentials, confirm AuraDB Free tier/region, freeze targets | Safe endpoints; actual managed regions recorded |
| 14:15-17:00 | Repository skeleton, pre-registration, dataset/checksums/query bank, result schema | Methodology committed before results |
| 17:00-22:00 | Core harness, Bolt family, FalkorDB and ArangoDB adapters, capped Podman setup | All targets connect, load tiny sample, and return equivalent results |
| 22:00-01:00 | Full MovieLens loads, correctness gate, query plans, ingest measurements | All targets valid or explicit pre-registered failure/fallback decision |
| 01:00-05:00 | Required read metrics and shortened complete concurrency sweep | Immutable raw result matrix complete |
| 05:00-07:15 | Statistics, charts, fairness analysis, README results matrix | `make report` produces final artifacts |
| 07:15-08:30 | Article, defense notes, clean-clone reproduction, CI and secret audit | No missing metric, placeholder, stale chart, or secret |
| 08:30-09:30 | Final review, publish repository/article, prepare submission email | Public signed-out review passes |
| 09:30-10:03 | Submission buffer | Email sent before deadline |

If implementation slips, cut p99 confidence polish, the open-loop bonus, video, and 256 MiB sensitivity in that order. Do not cut the four distinct competitor engines, required metrics, correctness, fairness disclosure, or reproducible README.

## 7. Reporting and communication plan

README order:

1. One-screen executive summary: three findings, no universal winner, largest fairness caveat.
2. Visual dashboard: ingest, traversal tails, saturation, reliability, and footprint.
3. What was compared and why.
4. Dataset/model and correctness proof.
5. Fairness dossier and managed-versus-controlled lenses.
6. Experimental design and query contract.
7. Full required results matrix.
8. Traversal by hop and degree bucket.
9. Lookup, aggregation, mixed-load saturation, and failure behavior.
10. Evidence-backed root-cause analysis.
11. Developer experience observations.
12. Decision guide by workload, not a winner leaderboard.
13. Reproduction, limitations, provenance, and raw artifacts.

For every important conclusion:

```text
Observation:
Evidence:
Potential explanation:
Confidence:
What would confirm it:
```

`ARTICLE.md` will use methodology as the hero. Its final title will be selected after results, avoiding a predetermined sensational claim. A 60-90 second demo will show `make doctor`, the correctness gate, one benchmark slice, and deterministic report generation.

Public launch is professional peer review, not manufactured engagement: publish under the candidate's identity, disclose the assessment context, invite technical criticism, respond substantively, correct genuine issues with commits, and report only real views/stars/comments.

## 8. Risks and pre-decided responses

| Risk | Decision |
|---|---|
| CognoDB memory statements conflict | Trust captured live allocation for primary cap; disclose every source and add 256 MiB sensitivity only if useful |
| Aura hardware is opaque | Keep Aura in managed-reality lens; never claim parity or pure-engine ranking |
| ArangoDB sizes itself from host RAM | Set both documented Arango resource-detection overrides and cgroup caps; verify logs |
| A capped engine cannot start or load | Tune only within the common cap; preserve OOM/failure evidence; make a documented go/no-go replacement decision by hour 20, not after seeing winners |
| 3-hop fan-out times out | Same query, result semantics, and timeout for all; report DNF/timeout rate; no platform-specific easier query |
| Driver protocols differ | Report end-to-end developer-observed latency; use logical query equivalence; do not claim protocol-neutral engine time |
| Mixed workload changes graph size | Use steady-state idempotent updates and verify post-run counts/digests |
| Cloud drift/noisy neighbors | Seeded target order plus three independent read sessions; preserve UTC/order/connection/client telemetry |
| Local containers have near-zero network distance | Treat local and managed targets as separate lenses; report network floor; never interpret cross-lens latency as pure engine performance |
| Podman CPU quota is not yet proven | Run an explicit cgroup/CPU-burn preflight; no official self-hosted result is valid until the 0.5 CPU limit is demonstrated |
| Only about 20.5 hours remain | Finish mandatory matrix and report first; reduce bonus repetitions/polish before cutting requirements |
| Free tier pauses | Separate fresh connection/wake behavior from warm query metrics and label it precisely |
| Time pressure | Protect five distinct databases, all required metrics, correctness, fairness, and README first; cut interactive UI, second dataset, and native-import appendix first |
| Public criticism finds a flaw | Preserve critique, fix transparently, invalidate/re-run affected rows, and update the decision log |

Fallback target policy: if ArangoDB cannot complete the smoke suite at the frozen cap after documented configuration and one bounded tuning attempt, replace it before official runs with current LadybugDB behind a small remote adapter service. The transport difference becomes an explicit caveat. Do not swap targets after performance results are known.

## 9. Ideas intentionally rejected or deferred

- No claim that managed hardware is equal when it is undisclosed.
- No automatic subtraction of RTT to invent "server time."
- No vendor numbers or prior candidate numbers in our results.
- No extrapolation from a dataset smaller than 100,000 relationships.
- No second dataset in the 48-hour critical path.
- No full benchmark across five additional managed clouds; account friction would threaten completeness.
- No reverse-engineering/gotcha investigation of CognoDB internals; it is high-risk and irrelevant to the rubric.
- No manual chart/table editing.
- No radar chart or interactive dashboard unless every required metric and audit gate is already complete.
- No public architecture explanation unsupported by query plans, telemetry, or cited documentation.

## 10. Definition of done

The submission is ready only when:

- CognoDB plus Neo4j, Memgraph, FalkorDB, and ArangoDB are represented and every required metric has a reported result or an explicit measured failure state.
- The resource-spec conflict and every deviation are visible near the top of the report.
- Identical source data, logical workloads, query bank, client, region policy, warm-up, and measurement policy are proven by artifacts.
- Correctness passes before performance publication.
- Official orchestration, report, audit, and packaging commands succeed from a clean clone with
  documented credentials.
- The full results matrix is generated from immutable raw records and contains no placeholder or hand-entered value.
- The README explains both what happened and what evidence supports each explanation.
- The public article/demo links work, the repository is accessible, and no secret exists in files, logs, artifacts, or Git history.
- The submission email uses the exact requested subject and is sent before the recorded 48-hour deadline.
