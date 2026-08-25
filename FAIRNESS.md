# Fairness Dossier

## Resource discrepancy

The assignment describes CognoDB c0 as burstable 0.5 vCPU, 256 MB RAM, and 1 GB disk. The live
candidate console on 2026-08-25 showed c0 as 512 MB RAM, burst to 0.5 vCPU, 1 GiB storage, up to
500 IOPS, 200 connections, engine v0.9.11, and a 50,000-row result cap. The primary controlled
cap is therefore frozen at the live allocation of 512 MiB, while the discrepancy remains visible.

## What each lens can support

| Lens | Supports | Does not support |
|---|---|---|
| Managed entry tier | Actual developer-visible free-tier experience from one client | Claims of equal hidden hardware or pure engine speed |
| Controlled local | Comparisons under the same client, host, network class and cgroup caps | Claims about managed operations, elasticity or WAN latency |

## Known caveats before measurement

| Caveat | Severity | Affected evidence | Likely bias | Mitigation | Residual risk |
|---|---|---|---|---|---|
| Local targets avoid Cairo-to-US network latency | High | Cross-lens latency | Favors local | Separate lenses; report fresh/warm protocol baselines | WAN and engine time cannot be separated |
| Aura hardware allocation is undisclosed | High | Managed resource parity | Unknown | Label not observable; avoid parity claims | Hidden contention/allocation remains |
| Cogno c0 can burst CPU | Medium | Managed throughput/latency | Time-dependent | Seed order and record UTC/session | Provider scheduling remains hidden |
| Windows host uses Podman through WSL2 | Medium | Controlled footprint/latency | Virtualization overhead | Same host and one active target | Engine-specific virtualization interaction |
| 512 MiB is extremely tight for JVM Neo4j | High | Neo4j reliability/latency | May disadvantage Neo4j | Preserve OOM/pressure evidence; never raise cap silently | GC/reclaim can dominate engine work |
| ArangoDB accepts an integer core override only | Medium | Arango controlled CPU | May expose more threads | Detect one core; cgroup enforces 0.5 CPU | Thread scheduling overhead differs |
| Official `library/arangodb` image logs an `enterprise` build string | Low | Arango edition labeling | Unknown | Label by official Community image repository and preserve exact startup log/digest | Packaging/build-string ambiguity remains |

The first Neo4j smoke attempt was OOM-killed during the first 3-hop correctness query after a
complete successful load. Before any official run, the query was rewritten to de-duplicate peer
vertices before expanding their ratings, preserving semantics while avoiding redundant path
materialization. Neo4j transaction memory was also explicitly capped at 32 MiB, heap at 128 MiB,
and page cache at 64 MiB. A second smoke attempt on Neo4j 2026.07.1 was OOM-killed after loading,
so the controlled target was moved to the supported 5.26 LTS line before official measurement.
The failed raw attempts remain in local provenance.

## Evidence gate

Before official runs, save container inspection, cgroup memory/CPU values, image digests,
the dedicated loopback mount and filesystem capacity, data-directory usage, service versions,
and managed tier/region evidence. If a cap is not enforced, the affected result cannot be called
controlled.
