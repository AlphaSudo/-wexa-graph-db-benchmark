# Decision Log

## 2026-08-25 - Dataset

Use MovieLens `ml-latest-small`: it is public, exceeds 100,000 relationships without sampling,
fits the smallest selected tier, and supports traversals, indexed filters and aggregation.

## 2026-08-25 - Comparison design

Use separate managed and controlled lenses because managed tiers do not disclose or permit exact
hardware parity. Keep a master matrix for assignment completeness, but constrain conclusions to
the evidence each lens can support.

## 2026-08-25 - Resource baseline

Use the live CognoDB c0 allocation, 0.5 burst CPU and 512 MiB RAM, as the controlled cap. Preserve
the assessment's 256 MB statement as a discrepancy rather than selecting it silently.

## 2026-08-25 - Failure policy

Correctness failure blocks performance publication. Runtime errors, timeouts, OOMs and throttling
remain visible. No result is estimated, extrapolated or copied from a vendor.

## 2026-08-25 - Neo4j 3-hop query and memory envelope

The first capped smoke run loaded the complete graph and passed counts, 1-hop and 2-hop checks,
then the container was OOM-killed during a path-multiplying 3-hop query. The logically equivalent
query now de-duplicates peer vertices before the final expansion. Explicit heap, page-cache and
transaction caps leave headroom inside the unchanged 512 MiB container limit. This decision was
made before official results and the failed smoke artifact is retained.

Neo4j 2026.07.1 later completed the load but was OOM-killed before the count gate, showing that
its baseline JVM/native footprint remained too close to the 512 MiB cgroup ceiling. The controlled
target therefore uses Neo4j Community 5.26 LTS, not a higher memory limit. It receives a fresh
volume because Neo4j stores cannot be downgraded. Both 2026 failure artifacts remain preserved.

The same transaction budget initially rejected an all-at-once graph reset while leaving the
server healthy. Reset now deletes bounded relationship batches before bounded node batches. This
keeps maintenance inside the declared resource envelope and does not affect measured workloads.

## 2026-08-25 - Common ingest operation

Use parameterized `CREATE`, not `MERGE`, for the primary driver-batched ingest. Every run resets
the graph, source IDs and edges are unique, and post-load validation detects duplicates. `MERGE`
therefore adds platform-dependent existence-check work that is not part of the logical ingest
contract. This was frozen before official measurement.

## 2026-08-25 - Aggregation numeric normalization

ArangoDB's AQL JSON response serializes whole-valued rating groups as integers, while the source
CSV and Cypher drivers expose the rating property as a float. The Arango adapter normalizes only
the aggregation group key to `float` before hashing. Counts and values are unchanged; this makes
the cross-language logical type contract explicit.

## 2026-08-25 - ArangoDB resource detection

ArangoDB initially logged host-wide memory and CPU detection even though its process was cgroup
capped. Set its supported detected-total-memory override to 512 MiB and detected-core override to
one core, the smallest integer value. Bound AQL memory, RocksDB cache/write buffers and RocksDB
workers explicitly. The cgroup remains authoritative at 0.5 CPU because ArangoDB cannot express
a fractional detected-core value. This change invalidates the earlier diagnostic smoke snapshot
and was frozen before official measurement. ArangoDB enforces a minimum of five total server
threads; that minimum is explicit while the 0.5-CPU cgroup quota controls their aggregate CPU.

## 2026-08-25 - FalkorDB persistence mode

An initial pilot explicitly enabled Redis AOF. Restarting the capped service then blocked on graph
module replay, making readiness depend on stale prior-run state. The primary controlled run now
explicitly disables Redis snapshots and AOF: FalkorDB remains an in-memory graph, reset starts
from an empty logical database, and its small persistent disk footprint is reported rather than
hidden. Timeout, no-eviction memory policy and one graph worker remain explicit. The BusyLoading
pilot artifact is retained and invalidated before official measurement.

## 2026-08-25 - ArangoDB image edition label

Use the pinned Docker Official Image `library/arangodb:3.12.7`, which the official image page
identifies as Community Edition; do not substitute the separate `arangodb/enterprise` repository.
The live binary prints an `enterprise` build string, so both the repository/digest and unchanged
startup log are published and the discrepancy is called out rather than silently relabeled.
