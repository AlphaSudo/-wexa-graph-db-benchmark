# Wexa Benchmark - Implementation and Submission Checklist

Use this as the execution control document. Do not check an item merely because code exists; check it only when the evidence named by the item exists. Requirement tags refer to the assessment: `A5.1` dataset, `A5.2` metrics, `A5.3` methodology, `A6` deliverables, `A7` standout work, `A8` evaluation, `A9` submission.

Owners: `[YOU]` candidate action, `[ME]` implementation/analysis action, `[JOINT]` review or externally consequential action.

## Gate 0 - Authority, deadline, and accounts

- [x] `G0-01` `[YOU]` Received 2026-08-24 10:03 Africa/Cairo; conservative deadline 2026-08-26 10:03 Africa/Cairo. (`A9`)
- [x] `G0-02` `[YOU]` Candidate name: Ahmed Yasser Morra. (`A9`)
- [x] `G0-03` `[JOINT]` Public repository approved and created under `AlphaSudo`; leading-hyphen rename remains recommended. (`A6`)
- [x] `G0-04` `[YOU]` GitHub CLI authenticated locally as `AlphaSudo`; token value was not copied into project files. (`A6`, `A9`)
- [ ] `G0-05` `[YOU]` Recreate/rotate the empty CognoDB c0 in `us-central1`; store the replacement credential only in ignored local configuration. (`A3`, `A5.3`, `A9`)
- [x] `G0-06` `[YOU]` Capture live CognoDB specs: c0, 512 MB, burst 0.5 vCPU, 1 GiB, up to 500 IOPS, 200 connections, v0.9.11. (`A5.3`, `A8`)
- [ ] `G0-07` `[YOU]` Confirm the Neo4j instance is AuraDB Free (not the visible 14-day trial) and is in `us-central1`; rotate the exposed credential. (`A4`, `A5.3`, `A9`)
- [x] `G0-08` `[YOU]` Budget frozen at zero; use managed free tiers and the local PC only. (`A5.3`)
- [x] `G0-09` `[ME]` Local preflight recorded: Windows 11 Pro, i7-1065G7 4C/8T, 7.8 GiB RAM, Podman 5.7.1 on WSL2, sufficient disk. (`A5.3`)
- [ ] `G0-10` `[JOINT]` Freeze region, resource cap `B`, target list, and fallback decision deadline before performance results. (`A5.3`, `A8`)

## Gate 1 - Fairness and pre-registration

- [x] `F-01` `[ME]` Save the assessment's 256 MB c0 statement as source evidence. (`A5.3`)
- [ ] `F-02` `[ME]` Save a dated copy/screenshot of current CognoDB pricing/spec documentation. (`A5.3`)
- [x] `F-03` `[ME]` Live c0 recorded: 512 MB, burst 0.5 vCPU, 1 GiB, 500 IOPS cap, 200 connections, v0.9.11, provisioned 2026-08-25. (`A5.3`)
- [x] `F-04` `[ME]` Define `B = 512 MiB` from the live c0 allocation; retain the assessment's 256 MB statement as a documented discrepancy. (`A5.3`, `A8`)
- [ ] `F-05` `[ME]` Record every target's deployment type, version/image digest, protocol, advertised limits, region, persistence, idle behavior, and observability. (`A5.3`, `A6`)
- [x] `F-06` `[ME]` Label AuraDB hardware as undisclosed unless official/live evidence states otherwise. (`A5.3`)
- [x] `F-07` `[ME]` Write the managed-reality and resource-controlled comparison lenses; define which claims each can support. (`A5.3`, `A8`)
- [x] `F-08` `[ME]` Pre-register dataset, indexes, query semantics, seed, warm-up, samples, repetitions, timeout, retries, exclusions, batch size, concurrency, mixes, open-loop rate, statistics, and charts. (`A5.3`)
- [x] `F-09` `[ME]` Create `docs/DECISIONS.md` entries for dataset, target set, topology, resource baseline, query contract, and failure policy. (`A7`)
- [x] `F-10` `[ME]` Create a caveats ledger with caveat, severity, direction of bias, affected results, mitigation, and residual risk. (`A5.3`, `A6`)
- [x] `F-11` `[ME]` Require a dated decision entry for every post-registration methodology change. (`A8`)

## Gate 2 - Repository, environment, and secrets

- [x] `R-01` `[ME]` Initialize the Git repository with a clear name and license. (`A6`)
- [x] `R-02` `[ME]` Add the planned package/repository structure from `WINNING_PLAN.md`. (`A6`, `A8`)
- [x] `R-03` `[ME]` Configure Python 3.11, `pyproject.toml`, and a committed fully pinned requirements lock. (`A6`, `A8`)
- [x] `R-04` `[ME]` Pin database image tags and record resolved image digests. (`A5.3`, `A8`)
- [x] `R-05` `[ME]` Add `.env.example` with names only and `.env`/credential/log exclusions in `.gitignore`. (`A9`)
- [ ] `R-06` `[YOU]` Populate the ignored local `.env`; never paste secrets into chat, issues, README, or commits. (`A9`)
- [x] `R-07` `[ME]` Add structured logging that redacts URI userinfo, passwords, tokens, and query parameters marked secret. (`A9`)
- [x] `R-08` `[ME]` Add Ruff, Pyright, Pytest, and deterministic formatting/lint targets. (`A8`)
- [ ] `R-09` `[ME]` Add CI for lint, types, unit tests, dataset-manifest test, and a tiny local smoke benchmark. (`A7`, `A8`)
- [ ] `R-10` `[ME]` Add secret scanning for the worktree and full Git history. (`A9`)
- [ ] `R-11` `[ME]` Add `make doctor`, `dataset`, `smoke`, `official`, `report`, and `audit`. (`A5.3`, `A6`, `A8`)

## Gate 3 - Infrastructure parity

- [x] `I-01` `[JOINT]` Select zero-cost local topology: one fixed Windows client and one-at-a-time Podman containers on the same PC. (`A5.3`)
- [x] `I-02` `[ME]` Record local OS, CPU, RAM, WSL2 kernel, Podman, Python/runtime, and free disk metadata. (`A5.3`, `A6`)
- [x] `I-03` `[ME]` Bind self-hosted database ports to localhost only; do not expose unauthenticated ports to the LAN/internet. (`A6`)
- [x] `I-04` `[ME]` Run exactly one self-hosted database target at a time. (`A5.3`)
- [x] `I-05` `[ME]` Prove and enforce 0.5 vCPU, 512 MiB memory, and no swap using Podman/cgroup v2 before accepting results. (`A5.3`)
- [x] `I-06` `[ME]` Create one 1 GiB loopback data filesystem per capped target and mount the correct data directory. (`A5.3`)
- [x] `I-07` `[ME]` Capture `docker inspect`, cgroup files, `df`, `du`, and container logs for resource proof. (`A5.3`, `A6`)
- [x] `I-08` `[ME]` Configure Neo4j heap/page cache inside the common cap and record settings. (`A5.3`)
- [x] `I-09` `[ME]` Configure Memgraph durability/storage mode consistently and record it. (`A5.3`)
- [x] `I-10` `[ME]` Configure FalkorDB persistence, timeout policy, query memory, and thread count consistently with the protocol. (`A5.3`)
- [x] `I-11` `[ME]` Set ArangoDB detected-memory and core overrides to 512 MiB/one integer core; retain the authoritative 0.5-CPU cgroup and verify logs. (`A5.3`)
- [ ] `I-12` `[ME]` Record managed target region, hostname, protocol/TLS, connection limit, and exposed metrics. (`A5.3`)
- [ ] `I-13` `[ME]` Verify the local client is not CPU/RAM-bound during pilot load; close unrelated applications and record client telemetry. (`A5.3`)

## Gate 4 - Dataset and graph model

- [x] `D-01` `[ME]` Download MovieLens `ml-latest-small` from the official source. (`A5.1`)
- [x] `D-02` `[ME]` Save source URL, retrieval UTC time, archive size, license/readme, and SHA-256. (`A5.1`, `A6`)
- [x] `D-03` `[ME]` Normalize users, movies, and ratings deterministically without dropping or synthesizing rating edges. (`A5.1`)
- [x] `D-04` `[ME]` Parse movie year deterministically; record null/parse rules. (`A5.1`, `A5.3`)
- [x] `D-05` `[ME]` Produce normalized CSV files and SHA-256 checksums. (`A5.1`, `A6`)
- [x] `D-06` `[ME]` Produce `data/manifest.json` with 610 users, 9,742 movies, 10,352 total nodes, and 100,836 relationships; fail on mismatch. (`A5.1`)
- [x] `D-07` `[ME]` Record property types, null counts, rating totals, year distribution, and degree distribution. (`A5.1`, `A8`)
- [x] `D-08` `[ME]` Generate the 100-start degree-stratified query bank using seed `20260825`. (`A5.2`, `A5.3`)
- [x] `D-09` `[ME]` Store query-bank IDs, bucket thresholds, and checksum in the repository. (`A5.3`, `A6`)
- [x] `D-10` `[ME]` Verify the final graph fits AuraDB Free's current documented node/relationship caps before load. (`A5.1`, `A5.3`)

## Gate 5 - Adapter and loader implementation

- [ ] `A-01` `[ME]` Define one typed adapter interface for lifecycle, schema, load, query, explain, footprint, and reset. (`A6`, `A8`)
- [x] `A-02` `[ME]` Implement shared Bolt adapter behavior for CognoDB, AuraDB, Neo4j CE, and Memgraph without copy-paste timing logic. (`A6`, `A8`)
- [x] `A-03` `[ME]` Implement CognoDB target configuration using only environment variables. (`A3`, `A9`)
- [x] `A-04` `[ME]` Implement AuraDB target configuration using only environment variables. (`A4`, `A9`)
- [x] `A-05` `[ME]` Implement Neo4j CE lifecycle/configuration. (`A4`, `A6`)
- [x] `A-06` `[ME]` Implement Memgraph lifecycle/configuration. (`A4`, `A6`)
- [x] `A-07` `[ME]` Implement FalkorDB adapter using its official Python client/Redis protocol. (`A4`, `A6`)
- [x] `A-08` `[ME]` Implement ArangoDB adapter and AQL translations. (`A4`, `A6`)
- [x] `A-09` `[ME]` Implement identical logical indexes and capture actual DDL/status per target. (`A5.2`, `A5.3`)
- [x] `A-10` `[ME]` Implement a common driver-batch size and order for the primary ingest comparison. (`A5.2`, `A5.3`)
- [x] `A-11` `[ME]` Make loaders reset-safe and independently time node, relationship, index, validation, and end-to-ready phases. (`A5.2`)
- [ ] `A-12` `[ME]` Add bounded retry only for classified transient errors; record every retry and final outcome. (`A5.3`)
- [ ] `A-13` `[ME]` Add per-operation timeout and connection-pool acquisition measurement. (`A5.3`, `A7`)
- [ ] `A-14` `[ME]` Complete a bounded smoke trial on all targets by hour 20 and freeze any fallback replacement before official results. (`A4`, `A5.3`)

## Gate 6 - Logical query contract and correctness

- [x] `C-01` `[ME]` Document exact intent, parameters, result shape, directedness, distinctness, ordering, and limits for every workload. (`A5.3`)
- [x] `C-02` `[ME]` Store every Cypher and AQL translation beside the canonical contract. (`A5.3`, `A6`)
- [x] `C-03` `[ME]` Unit-test result normalization across adapter response shapes. (`A8`)
- [x] `C-04` `[ME]` Validate exact node and relationship counts after each load. (`A5.1`)
- [x] `C-05` `[ME]` Validate unique `userId` and `movieId` counts. (`A5.1`, `A5.3`)
- [x] `C-06` `[ME]` Validate no unexpected duplicate rating edge key. (`A5.1`, `A5.3`)
- [x] `C-07` `[ME]` Validate deterministic property aggregates against source manifest. (`A5.3`)
- [x] `C-08` `[ME]` Validate 100 fixed node degrees and normalized 1/2/3-hop adjacency hashes. (`A5.3`, `A7`)
- [x] `C-09` `[ME]` Validate result cardinality and digest for 1/2/3-hop, point, filtered, and aggregation workloads. (`A5.3`)
- [x] `C-10` `[ME]` Validate graph counts after every mixed cell and the full integrity contract after all writes. (`A5.3`)
- [x] `C-11` `[ME]` Capture unmeasured `EXPLAIN` evidence for point, filtered, 3-hop, and aggregation. (`A7`)
- [x] `C-12` `[ME]` Enforce `VALIDATION_FAILED -> publication blocked`; preserve diagnostics in the run ledger. (`A5.3`, `A8`)

## Gate 7 - Required metrics

### Ingest

- [ ] `M-I01` `[ME]` Run every target from a verified empty logical database. (`A5.2`)
- [ ] `M-I02` `[ME]` Measure nodes/s, relationships/s, node load time, relationship load time, index time, validation time, and total end-to-ready wall time. (`A5.2`)
- [ ] `M-I03` `[ME]` Perform three ingest repetitions or explicitly record why a managed target prevents it. (`A7`, `A8`)
- [x] `M-I04` `[ME]` Keep native bulk import out of the primary common-path metric; label any optional native run separately. (`A5.3`)

### Traversals, lookups, aggregation

- [ ] `M-R01` `[ME]` Warm each target with 30 unmeasured operations per read workload. (`A5.2`, `A5.3`)
- [ ] `M-R02` `[ME]` Run at least 100 measured 1-hop operations per target/session. (`A5.2`)
- [ ] `M-R03` `[ME]` Run at least 100 measured 2-hop operations per target/session. (`A5.2`)
- [ ] `M-R04` `[ME]` Run at least 100 measured 3-hop operations per target/session. (`A5.2`)
- [ ] `M-R05` `[ME]` Run at least 100 measured indexed point lookups per target/session. (`A5.2`)
- [ ] `M-R06` `[ME]` Run at least 100 measured indexed/filtered lookups per target/session. (`A5.2`)
- [ ] `M-R07` `[ME]` Run at least 100 measured group-by aggregations per target/session and consume full results. (`A5.2`)
- [ ] `M-R08` `[ME]` Repeat official read sessions three times. (`A7`, `A8`)
- [ ] `M-R09` `[ME]` Capture p50 and p95 for every required read cell. (`A5.2`)
- [x] `M-R10` `[ME]` Also capture p99, min/max, MAD/CV, valid N, bootstrap CI, errors, timeouts, and retries. (`A7`, `A8`)
- [x] `M-R11` `[ME]` Report degree-bucket traversal results as analysis, retaining combined results as the primary table. (`A5.2`, `A7`)
- [x] `M-R12` `[ME]` Separate five fresh-connection observations from warmed pooled query results. (`A5.3`, `A7`)

### Mixed workload

- [x] `M-X01` `[ME]` Implement steady-state idempotent writes that do not grow the graph. (`A5.2`, `A5.3`)
- [ ] `M-X02` `[ME]` Run 95/5 and 80/20 read/write mixes. (`A5.2`, `A7`)
- [ ] `M-X03` `[ME]` Run concurrency 1, 5, 10, 20, and 40 for 60 seconds each on every target. (`A5.2`, `A7`)
- [ ] `M-X04` `[ME]` Run three interleaved sessions with seeded platform order. (`A5.3`, `A7`)
- [ ] `M-X05` `[ME]` Run one open-loop 80/20 test at the pre-registered common arrival rate. (`A7`, `A8`)
- [x] `M-X06` `[ME]` Report offered/achieved QPS, p50/p95/p99, valid N, reads/writes, retries, errors, timeouts, and reconnects. (`A5.2`, `A7`)
- [ ] `M-X07` `[ME]` Identify peak sustainable throughput, latency knee, first-error concurrency, and collapse point without hiding failed levels. (`A7`, `A8`)
- [x] `M-X08` `[ME]` Verify graph counts after each mixed cell and integrity aggregates after the mixed workload. (`A5.3`)

### Footprint and supporting baselines

- [x] `M-F01` `[ME]` Sample self-hosted memory, CPU, I/O and PIDs each second; capture disk/restart/cgroup evidence at run boundaries. (`A5.2`)
- [ ] `M-F02` `[ME]` Record managed storage/memory/CPU/instance metrics where exposed; use exact `not observable` elsewhere. (`A5.2`)
- [x] `M-F03` `[ME]` Capture five fresh protocol connections and warm pooled `RETURN 1` distribution for every target. (`A5.3`, `A7`)
- [ ] `M-F04` `[ME]` Record client CPU/RAM and pool-wait telemetry during every throughput run. (`A5.3`)
- [x] `M-F05` `[ME]` Do not subtract network baseline and label the remainder as server execution time. (`A5.3`, `A8`)

## Gate 8 - Run orchestration and provenance

- [x] `O-01` `[ME]` Seed and persist the official one-at-a-time target order. (`A5.3`)
- [x] `O-02` `[ME]` Use immutable run IDs and append-only raw JSONL. (`A6`, `A8`)
- [x] `O-03` `[ME]` Store UTC timestamps, git SHA, config hash, dataset hash, query-bank hash, target version/digest, client metadata, and attempt number in every record. (`A6`, `A8`)
- [x] `O-04` `[ME]` Preserve failed runs and invalidation reasons; never overwrite or delete them from provenance. (`A5.3`)
- [x] `O-05` `[ME]` Classify timeout, connection, throttling, validation, OOM, server, and client errors. (`A5.3`, `A7`)
- [x] `O-06` `[ME]` Ensure raw artifacts never contain credentials or full secret-bearing URIs. (`A9`)
- [x] `O-07` `[ME]` Audit all expected target/read-session/mixed/resource/plan cells from config. (`A5.2`, `A6`)
- [ ] `O-08` `[ME]` Make `make audit` fail on missing cells, missing provenance, checksum mismatch, stale chart/table, placeholder text, or detected secret. (`A6`, `A8`, `A9`)

## Gate 9 - Analysis and generated artifacts

- [ ] `P-01` `[ME]` Generate the complete required results matrix for every target. (`A6`)
- [ ] `P-02` `[ME]` Generate resource/spec and fairness-deviation tables. (`A5.3`, `A6`)
- [ ] `P-03` `[ME]` Generate ingest nodes/s and relationships/s chart with total-time context. (`A6`, `A7`)
- [ ] `P-04` `[ME]` Generate traversal p50/p95/p99 by hop chart. (`A6`, `A7`)
- [ ] `P-05` `[ME]` Generate traversal latency-versus-degree analysis. (`A7`)
- [ ] `P-06` `[ME]` Generate lookup and aggregation latency/reliability chart. (`A6`)
- [ ] `P-07` `[ME]` Generate throughput-versus-concurrency and p95-versus-concurrency charts. (`A7`)
- [ ] `P-08` `[ME]` Generate failure/timeout and footprint tables/charts. (`A5.2`, `A6`)
- [ ] `P-09` `[ME]` Show confidence intervals/variance and valid sample counts. (`A7`, `A8`)
- [ ] `P-10` `[ME]` Label managed-entry and controlled-engine findings separately. (`A5.3`, `A8`)
- [ ] `P-11` `[ME]` Write each headline finding as observation, evidence, possible explanation, confidence, and confirming evidence needed. (`A6`, `A8`)
- [ ] `P-12` `[ME]` Refuse a universal winner; write a workload-based decision guide. (`A2`, `A6`)
- [ ] `P-13` `[ME]` Separate facts from hypotheses and cite official architecture documentation/query plans where used. (`A6`, `A8`)

## Gate 10 - Deliverables and communication

- [ ] `W-01` `[ME]` README opens with one-screen executive summary, three findings, and largest fairness caveat. (`A6`, `A8`)
- [ ] `W-02` `[ME]` README contains platform choice rationale and full spec/deviation table. (`A6`, `A7`)
- [x] `W-03` `[ME]` README contains exact dataset source, license/readme, counts, model, and checksums. (`A5.1`, `A6`)
- [ ] `W-04` `[ME]` README contains load method and index policy per target. (`A5.1`, `A5.2`, `A6`)
- [ ] `W-05` `[ME]` README contains correctness proof and query translation contract. (`A5.3`, `A6`)
- [ ] `W-06` `[ME]` README contains every metric from assessment section 5.2 for every target. (`A5.2`, `A6`)
- [ ] `W-07` `[ME]` README contains methodology, warm-up, repetitions, ordering, timeouts, retries, client, region, and resource proof. (`A5.3`, `A6`)
- [ ] `W-08` `[ME]` README contains analysis, caveats, limitations, failure behavior, and no unsupported causal claim. (`A6`, `A7`)
- [ ] `W-09` `[ME]` README contains a five-minute smoke path and full reproduction path. (`A6`, `A8`)
- [x] `W-10` `[ME]` `REPRODUCING.md` lets a free-tier account holder rerun from a clean clone. (`A6`)
- [ ] `W-11` `[ME]` `ARTICLE.md` is publishable, methodology-led, accurate, and linked to raw evidence. (`A7`, `A8`)
- [ ] `W-12` `[JOINT]` Produce/approve a 60-90 second technical walkthrough. (`A7`, `A8`)
- [ ] `W-13` `[YOU]` Publish the article under your identity and share it to selected relevant communities without spam. (`A7`, `A8`)
- [ ] `W-14` `[JOINT]` Respond to genuine critique; log fixes and invalidate/re-run affected results. (`A7`, `A8`)
- [ ] `W-15` `[ME]` Add only real engagement receipts; never fabricate stars, views, or comments. (`A7`, `A8`)
- [ ] `W-16` `[ME]` Prepare concise interview defense notes for every major design choice and caveat. (`A10`)

## Gate 11 - Final audit and submission

- [ ] `S-01` `[ME]` Run lint, type checks, unit/integration tests, report regeneration, and rubric audit. (`A6`, `A8`)
- [ ] `S-02` `[ME]` Clone into a clean directory and execute README smoke path using only documented steps. (`A6`, `A8`)
- [ ] `S-03` `[ME]` Verify every command, internal link, web link, chart, table, and raw artifact. (`A6`)
- [ ] `S-04` `[ME]` Verify no placeholder, invented result, extrapolation, missing target cell, or silently discarded failure. (`A5.2`, `A5.3`)
- [ ] `S-05` `[ME]` Secret-scan the worktree, untracked files, result artifacts, logs, and full Git history. (`A9`)
- [ ] `S-06` `[ME]` Verify the public repository URL in a signed-out browser. (`A6`, `A9`)
- [ ] `S-07` `[ME]` Verify CI is green at the submitted commit and record the commit SHA in the email draft. (`A8`)
- [ ] `S-08` `[JOINT]` Review the executive summary and every headline claim against raw evidence. (`A6`, `A8`)
- [ ] `S-09` `[YOU]` Rotate/revoke benchmark credentials after the final run if appropriate. (`A9`)
- [ ] `S-10` `[YOU]` Email `hr@wexa.ai` with subject `CognoDB Assignment 1 – <Your Name>` and repository URL. (`A9`)
- [ ] `S-11` `[YOU]` Send before the exact recorded 48-hour deadline and retain sent-mail proof. (`A9`)

## Final scorecard - no-go if any red cell remains

- [ ] Methodology/fairness: same source data, logical queries, client, region policy, warm-up, cap evidence, deviations, and caveats are visible.
- [ ] Completeness: all required metric cells exist for every target, including explicit failure states.
- [ ] Reproducibility/code: clean-clone commands work, dependencies/images are pinned, raw results regenerate the report, CI is green.
- [ ] README/analysis: full matrix and charts are readable; conclusions are evidence-backed and limitations are prominent.
- [ ] Communication: article/demo are accurate, public, linked, and capable of standing alone for a broad technical audience.
- [ ] Security/submission: no secrets anywhere; repository access and email subject/deadline are correct.
