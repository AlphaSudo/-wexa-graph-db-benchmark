# Frozen Benchmark Methodology

This document is the pre-registration contract. Any material change after the first official
measurement must be recorded in `docs/DECISIONS.md`, including whether previous runs were
invalidated.

## Comparison lenses

The managed lens compares CognoDB c0 with confirmed AuraDB Free from the same Cairo client and,
where provisioning permits, the same `us-central1` region. Provider CPU and memory that are not
observable are reported as such.

The controlled lens compares Neo4j Community, Memgraph, FalkorDB, and ArangoDB one at a time on
the same Podman machine. Each service is configured for 0.5 CPU, 512 MiB container memory,
512 MiB memory-plus-swap, and its own 1 GiB ext4 loopback data filesystem. Storage capacity,
cgroup enforcement, and the mounted database data directory are evidence gates, not assumptions.

## Dataset and schema

MovieLens `ml-latest-small` produces `User` and `Movie` vertices and directed `RATED` edges.
The expected counts are 610 users, 9,742 movies, and 100,836 ratings. Logical indexes are unique
user ID, unique movie ID, and a secondary movie-year index. Platform-specific DDL may differ,
but the logical index contract does not.

The common ingest path resets each graph, creates indexes/constraints, and sends equivalent
parameterized `CREATE` batches. Existence-checking `MERGE` is intentionally excluded because the
source keys are unique and the reset/correctness gates already enforce an empty, duplicate-free
load. Native bulk loaders may appear only as a separately labeled appendix.

## Workload contract

- 1-hop: movie IDs directly rated by a selected user.
- 2-hop: distinct peer user IDs connected through a rated movie, excluding the start user.
- 3-hop: distinct movie IDs reached through a peer user.
- Point lookup: movie by indexed movie ID.
- Filtered lookup: movie IDs by indexed year.
- Aggregation: relationship count grouped by rating value.
- Mixed write: assign an idempotent benchmark token to a selected user; graph size cannot grow.

All result sets are fully consumed, normalized into stable JSON, and hashed. Query translation
digests must agree before the target becomes benchmark-eligible.

## Sampling and timing

- Seed: `20260825`.
- Traversal starts: 25 users from each rank bucket: bottom 25%, middle 50%, 75th-95th%, top 5%.
- Read warm-up: 30 unmeasured operations per workload and target.
- Read measurement: 100 operations per workload in each of three independent sessions.
- Clock: `time.perf_counter_ns()` around the complete client call and result consumption.
- Required percentiles: p50 and p95; also report p99, min, max, valid N, errors, and timeouts.
- Percentiles include successful observations only and are always shown beside failure counts.

## Mixed workload

Closed-loop sweeps use concurrency 1, 5, 10, 20, and 40 for 60 seconds at 95/5 and 80/20
read/write mixes. One 80/20 open-loop run offers 100 operations/second for 60 seconds and records
latency from the intended send time so queuing is not hidden.

## Failure and retry policy

Default timeout is 15 seconds. Official read operations are not automatically retried because a
retry changes the latency distribution. Connection establishment may retry only during readiness
checks and is recorded separately. Timeouts and errors remain raw records. A success rate below
95% is presented as a reliability failure, not as a fast successful-query result.

## Order and environment

The one-at-a-time controlled topology uses the seeded target order stored in the official config;
each target completes as a unit so stopped local databases do not gain from hidden background
resource use. The run header stores full client metadata and target order; every record stores its
run ID, UTC time, order hash/index, deployment type, config/dataset/query-bank hashes, and Git
commit. Fresh-connection timing and warm `RETURN 1` provide supporting network/protocol baselines;
they are not subtracted from query latency.
