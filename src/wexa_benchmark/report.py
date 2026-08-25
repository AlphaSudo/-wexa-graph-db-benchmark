from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import AppConfig
from .results import read_records, result_paths
from .stats import summarize
from .util import sha256_file


def generate_report(config: AppConfig, repository_root: Path) -> tuple[Path, Path]:
    current_query_bank = sha256_file(repository_root / "data" / "query_bank.json")
    runs = _latest_valid_runs(config, repository_root, current_query_bank)
    report = {
        "schema_version": 1,
        "config_sha256": config.sha256,
        "query_bank_sha256": current_query_bank,
        "run_label": config.run_label,
        "targets": {
            target_id: _target_report(target_id, runs.get(target_id))
            for target_id, target in config.targets.items()
            if target.enabled
        },
    }
    output_root = repository_root / "results" / "generated"
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{config.run_label}-summary.json"
    markdown_path = output_root / f"{config.run_label}-summary.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _latest_valid_runs(
    config: AppConfig, repository_root: Path, query_bank_sha256: str
) -> dict[str, list[dict[str, Any]]]:
    matches: dict[str, list[tuple[Path, list[dict[str, Any]]]]] = defaultdict(list)
    for path in result_paths(repository_root / "results" / "raw"):
        records = read_records(path)
        if not records:
            continue
        first = records[0]
        if first.get("config_sha256") != config.sha256:
            continue
        if first.get("query_bank_sha256") != query_bank_sha256:
            continue
        if not any(
            record.get("record_type") == "lifecycle" and record.get("state") == "BENCHMARKED"
            for record in records
        ):
            continue
        matches[str(first["target_id"])].append((path, records))
    return {target_id: values[-1][1] for target_id, values in matches.items()}


def _target_report(target_id: str, records: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not records:
        return {"target_id": target_id, "status": "missing"}
    loads = {
        str(record["phase"]): {
            "items": record["items"],
            "duration_ms": record["duration_ms"],
            "items_per_second": record["items_per_second"],
        }
        for record in records
        if record.get("record_type") == "load_phase"
    }
    ingest_summary = next(
        (record for record in records if record.get("record_type") == "ingest_summary"),
        None,
    )
    reads: dict[str, Any] = {}
    workloads = sorted(
        {
            str(record["workload"])
            for record in records
            if record.get("record_type") == "read_sample"
        }
    )
    for workload in workloads:
        samples = [
            record
            for record in records
            if record.get("record_type") == "read_sample" and record.get("workload") == workload
        ]
        durations = [float(record["duration_ms"]) for record in samples if record.get("success")]
        reads[workload] = summarize(durations, len(samples))
    reads_by_degree: dict[str, Any] = {}
    for workload in ("hop_1", "hop_2", "hop_3"):
        for bucket in ("low", "medium", "high", "hub"):
            samples = [
                record
                for record in records
                if record.get("record_type") == "read_sample"
                and record.get("workload") == workload
                and record.get("degree_bucket") == bucket
            ]
            durations = [
                float(record["duration_ms"]) for record in samples if record.get("success")
            ]
            if samples:
                reads_by_degree[f"{workload}/{bucket}"] = summarize(durations, len(samples))
    mixed = [
        {
            key: record.get(key)
            for key in (
                "model",
                "mix",
                "read_ratio",
                "concurrency",
                "offered_qps",
                "achieved_qps",
                "attempts",
                "successes",
                "failures",
                "success_rate",
                "p50_ms",
                "p95_ms",
                "p99_ms",
                "read_attempts",
                "write_attempts",
                "timeouts",
                "errors",
            )
        }
        for record in records
        if record.get("record_type") == "mixed_summary"
    ]
    validation = next(
        (
            record
            for record in reversed(records)
            if record.get("record_type") == "validation_summary"
        ),
        None,
    )
    connection = next(
        (record for record in records if record.get("record_type") == "connection"), None
    )
    resource = next(
        (record for record in reversed(records) if record.get("record_type") == "resource_summary"),
        None,
    )
    query_plans = {
        str(record["workload"]): {
            "success": bool(record.get("success")),
            "summary": _plan_summary(record.get("plan")),
        }
        for record in records
        if record.get("record_type") == "query_plan"
    }
    fresh_connection = next(
        (record for record in records if record.get("record_type") == "fresh_connection_summary"),
        None,
    )
    return {
        "target_id": target_id,
        "status": "complete",
        "run_id": records[0]["run_id"],
        "engine_version": connection.get("engine_version") if connection else "not observable",
        "validation_passed": bool(validation and validation.get("passed")),
        "load": loads,
        "ingest_summary": ingest_summary,
        "reads": reads,
        "reads_by_degree": reads_by_degree,
        "mixed": mixed,
        "resource": resource,
        "query_plans": query_plans,
        "fresh_connection": fresh_connection,
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {str(report['run_label']).title()} Benchmark Summary",
        "",
        "Generated from append-only raw JSONL. Missing cells are never estimated.",
        "",
        "## Ingest",
        "",
        "| Target | Status | End-to-ready s | All nodes/s | Relationships/s |",
        "|---|---|---:|---:|---:|",
    ]
    for target_id, target in report["targets"].items():
        ingest = target.get("ingest_summary") or {}
        lines.append(
            "| {target} | {status} | {duration} | {nodes} | {relationships} |".format(
                target=target_id,
                status=target["status"],
                duration=_seconds(ingest.get("duration_ms")),
                nodes=_number(ingest.get("nodes_per_second")),
                relationships=_number(ingest.get("relationships_per_second")),
            )
        )
    lines.extend(
        [
            "",
            "## Read latency",
            "",
            "| Target | Workload | p50 ms | p95 ms | p99 ms | p50 CI95 ms | CV | "
            "Successes | Failures |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for target_id, target in report["targets"].items():
        for workload, stats in target.get("reads", {}).items():
            lines.append(
                f"| {target_id} | {workload} | {_number(stats['p50_ms'])} | "
                f"{_number(stats['p95_ms'])} | {_number(stats['p99_ms'])} | "
                f"{_number(stats['p50_ci95_low_ms'])}-{_number(stats['p50_ci95_high_ms'])} | "
                f"{_number(stats['cv'])} | "
                f"{stats['successes']} | {stats['failures']} |"
            )
    lines.extend(
        [
            "",
            "## Traversal latency by source-degree bucket",
            "",
            "| Target | Hop/bucket | p50 ms | p95 ms | p99 ms | Valid N | Failures |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for target_id, target in report["targets"].items():
        for cell, stats in target.get("reads_by_degree", {}).items():
            lines.append(
                f"| {target_id} | {cell} | {_number(stats['p50_ms'])} | "
                f"{_number(stats['p95_ms'])} | {_number(stats['p99_ms'])} | "
                f"{stats['successes']} | {stats['failures']} |"
            )
    lines.extend(
        [
            "",
            "## Mixed workload",
            "",
            "| Target | Model | Mix | Concurrency | Offered QPS | Achieved QPS | "
            "p50/p95/p99 ms | R/W attempts | Errors/timeouts |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for target_id, target in report["targets"].items():
        for mixed in target.get("mixed", []):
            lines.append(
                f"| {target_id} | {mixed['model']} | {mixed['mix']} | "
                f"{mixed['concurrency']} | {_number(mixed['offered_qps'])} | "
                f"{_number(mixed['achieved_qps'])} | {_number(mixed['p50_ms'])}/"
                f"{_number(mixed['p95_ms'])}/{_number(mixed['p99_ms'])} | "
                f"{mixed['read_attempts']}/{mixed['write_attempts']} | "
                f"{mixed['errors']}/{mixed['timeouts']} |"
            )
    lines.extend(
        [
            "",
            "## Controlled resource footprint",
            "",
            "| Target | Samples | CPU p95/max % | Memory p95/peak MiB | "
            "Data directory MiB | Filesystem used/capacity MiB |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for target_id, target in report["targets"].items():
        resource = target.get("resource") or {}
        disk = resource.get("disk") or {}
        lines.append(
            f"| {target_id} | {resource.get('samples', 'not observable')} | "
            f"{_number(resource.get('cpu_percent_p95'))}/"
            f"{_number(resource.get('cpu_percent_max'))} | "
            f"{_mib(resource.get('memory_bytes_p95'))}/{_mib(resource.get('memory_bytes_peak'))} | "
            f"{_mib(disk.get('data_directory_bytes'))} | "
            f"{_mib(disk.get('used_bytes'))}/{_mib(disk.get('capacity_bytes'))} |"
        )
    lines.extend(
        [
            "",
            "## Unmeasured query-plan evidence",
            "",
            "| Target | Workload | Captured | Plan operators |",
            "|---|---|---|---|",
        ]
    )
    for target_id, target in report["targets"].items():
        for workload, plan in target.get("query_plans", {}).items():
            lines.append(f"| {target_id} | {workload} | {plan['success']} | {plan['summary']} |")
    lines.extend(
        [
            "",
            "## Supporting connection baselines",
            "",
            "These client-observed values are not subtracted from workload latency.",
            "",
            "| Target | Fresh connect p50/p95 ms | Warm pooled RETURN 1 p50/p95 ms | Failures |",
            "|---|---:|---:|---:|",
        ]
    )
    for target_id, target in report["targets"].items():
        fresh = target.get("fresh_connection") or {}
        pooled = target.get("reads", {}).get("return_1", {})
        lines.append(
            f"| {target_id} | {_number(fresh.get('p50_ms'))}/"
            f"{_number(fresh.get('p95_ms'))} | {_number(pooled.get('p50_ms'))}/"
            f"{_number(pooled.get('p95_ms'))} | "
            f"{fresh.get('failures', 'missing')}/{pooled.get('failures', 'missing')} |"
        )
    lines.append("")
    return "\n".join(lines)


def _number(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, int):
        return str(value)
    return f"{float(value):.3f}"


def _seconds(milliseconds: Any) -> str:
    if milliseconds is None:
        return "missing"
    return f"{float(milliseconds) / 1000:.3f}"


def _mib(value: Any) -> str:
    if value is None:
        return "not observable"
    return f"{float(value) / (1024 * 1024):.2f}"


def _plan_summary(plan: Any) -> str:
    if not isinstance(plan, dict):
        return "not observable"
    plan_format = plan.get("format")
    if plan_format == "neo4j_plan":
        operators: list[str] = []

        def visit(node: dict[str, Any]) -> None:
            operators.append(str(node.get("operator_type", "unknown")))
            for child in node.get("children", []):
                visit(child)

        visit(plan.get("root", {}))
        return " > ".join(operators)
    if plan_format == "falkordb_plan":
        return " > ".join(str(line).strip() for line in plan.get("lines", []))
    if plan_format == "aql_plan":
        return " > ".join(str(node.get("type")) for node in plan.get("nodes", []))
    if plan_format == "records":
        return " > ".join(str(next(iter(row.values()), "")).strip() for row in plan.get("rows", []))
    return str(plan_format or "not observable")
