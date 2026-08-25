from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import AppConfig
from .results import read_records, read_result_text, result_paths
from .util import sha256_file

REQUIRED_READS = {
    "return_1",
    "hop_1",
    "hop_2",
    "hop_3",
    "point_lookup",
    "filtered_lookup",
    "aggregation",
}
REQUIRED_PLANS = {"point_lookup", "filtered_lookup", "hop_3", "aggregation"}


def audit_results(config: AppConfig, repository_root: Path) -> dict[str, Any]:
    raw_root = repository_root / "results" / "raw"
    files = result_paths(raw_root)
    issues: list[str] = []
    completed_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    query_bank_path = repository_root / "data" / "query_bank.json"
    current_query_bank_sha256 = sha256_file(query_bank_path) if query_bank_path.exists() else None

    for path in files:
        text = read_result_text(path)
        lowered = text.lower()
        for marker in ("bolt+s://", "neo4j+s://", '"password":', "replace_me"):
            if marker in lowered:
                issues.append(f"Secret or placeholder marker {marker!r} found in {path.name}")
        records = read_records(path)
        if not records:
            issues.append(f"Empty raw result file: {path.name}")
            continue
        if any(
            record.get("record_type") == "lifecycle" and record.get("state") == "BENCHMARKED"
            for record in records
        ):
            completed_by_target[str(records[0]["target_id"])].append(
                {"path": path, "records": records}
            )

    for target_id, target in config.targets.items():
        if not target.enabled:
            continue
        runs = completed_by_target.get(target_id, [])
        if not runs:
            issues.append(f"No completed run for enabled target {target_id}")
            continue
        latest = runs[-1]["records"]
        required_provenance = {
            "run_id",
            "target_id",
            "config_sha256",
            "dataset_sha256",
            "query_bank_sha256",
            "git_commit",
            "recorded_at_utc",
        }
        missing_provenance = required_provenance - set(latest[0])
        if missing_provenance:
            issues.append(f"{target_id} lacks provenance fields: {sorted(missing_provenance)}")
        if config.run_label == "official" and latest[0].get("git_commit") == "uncommitted":
            issues.append(f"Official run for {target_id} has no Git commit")
        if latest[0].get("config_sha256") != config.sha256:
            issues.append(f"Latest completed run for {target_id} used a stale config")
        if latest[0].get("query_bank_sha256") != current_query_bank_sha256:
            issues.append(f"Latest completed run for {target_id} used a stale query bank")
        validation = [
            record for record in latest if record.get("record_type") == "validation_summary"
        ]
        if not validation or not validation[-1].get("passed"):
            issues.append(f"Latest completed run for {target_id} lacks a passing validation gate")
        reads = {
            str(record.get("workload"))
            for record in latest
            if record.get("record_type") == "read_summary"
        }
        missing_reads = REQUIRED_READS - reads
        if missing_reads:
            issues.append(f"{target_id} is missing read summaries: {sorted(missing_reads)}")
        for workload in REQUIRED_READS:
            summaries = [
                record
                for record in latest
                if record.get("record_type") == "read_summary"
                and record.get("workload") == workload
            ]
            if len(summaries) != config.benchmark.sessions:
                issues.append(
                    f"{target_id}/{workload} has {len(summaries)} sessions; "
                    f"expected {config.benchmark.sessions}"
                )
            if any(
                int(summary.get("attempts", 0)) != config.benchmark.measured_operations
                for summary in summaries
            ):
                issues.append(f"{target_id}/{workload} has an incorrect measured sample count")
        load_phases = {
            str(record.get("phase"))
            for record in latest
            if record.get("record_type") == "load_phase"
        }
        if load_phases != {"load_users", "load_movies", "load_ratings"}:
            issues.append(f"{target_id} has incomplete load phases: {sorted(load_phases)}")
        if not any(record.get("record_type") == "ingest_summary" for record in latest):
            issues.append(f"{target_id} lacks an end-to-ready ingest summary")
        fresh = [
            record for record in latest if record.get("record_type") == "fresh_connection_summary"
        ]
        if not fresh or int(fresh[-1].get("attempts", 0)) != 5:
            issues.append(f"{target_id} lacks the five-sample fresh connection baseline")
        mixed = [record for record in latest if record.get("record_type") == "mixed_summary"]
        expected_closed = {
            (mix, concurrency)
            for mix in config.benchmark.mixes
            for concurrency in config.benchmark.mixed_concurrency
        }
        actual_closed = {
            (str(record.get("mix")), int(record.get("concurrency", -1)))
            for record in mixed
            if record.get("model") == "closed_loop"
        }
        if actual_closed != expected_closed:
            issues.append(f"{target_id} has incomplete closed-loop cells")
        if len([record for record in mixed if record.get("model") == "open_loop"]) != 1:
            issues.append(f"{target_id} does not have exactly one open-loop summary")
        if any(record.get("p95_ms") is None for record in mixed):
            issues.append(f"{target_id} has a mixed cell without p95 latency")
        final_validation = [
            record for record in latest if record.get("record_type") == "post_run_validation"
        ]
        if not final_validation or not final_validation[-1].get("passed"):
            issues.append(f"{target_id} lacks passing post-run validation")
        plans = {
            str(record.get("workload")): bool(record.get("success"))
            for record in latest
            if record.get("record_type") == "query_plan"
        }
        missing_plans = REQUIRED_PLANS - set(plans)
        failed_plans = sorted(workload for workload, passed in plans.items() if not passed)
        if missing_plans:
            issues.append(f"{target_id} is missing query plans: {sorted(missing_plans)}")
        if failed_plans:
            issues.append(f"{target_id} has failed query plans: {failed_plans}")
        if target.deployment == "controlled-local":
            resources = [
                record for record in latest if record.get("record_type") == "resource_summary"
            ]
            if not resources or not resources[-1].get("passed"):
                issues.append(f"{target_id} lacks passing resource/footprint evidence")

    return {
        "passed": not issues,
        "raw_files": len(files),
        "completed_targets": sorted(completed_by_target),
        "issues": issues,
    }
