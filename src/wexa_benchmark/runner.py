from __future__ import annotations

import itertools
import random
import time
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .adapters import GraphAdapter, create_adapter
from .config import AppConfig, TargetConfig
from .dataset import (
    PreparedDataset,
    read_movies,
    read_ratings,
    read_users,
)
from .resources import ResourceSampler
from .results import ResultWriter
from .stats import summarize
from .util import (
    batched,
    classify_error,
    client_metadata,
    git_commit,
    normalized_rows,
    stable_digest,
)

READ_WORKLOADS = ("hop_1", "hop_2", "hop_3", "point_lookup", "filtered_lookup", "aggregation")


def run_target(
    config: AppConfig,
    target: TargetConfig,
    dataset: PreparedDataset,
    repository_root: Path,
) -> Path:
    run_id = _run_id(config.run_label, target.target_id)
    output_path = repository_root / "results" / "raw" / f"{run_id}.jsonl"
    writer = ResultWriter(
        output_path,
        {
            "schema_version": 1,
            "run_id": run_id,
            "run_label": config.run_label,
            "target_id": target.target_id,
            "deployment": target.deployment,
            "config_sha256": config.sha256,
            "dataset_sha256": dataset.manifest["sha256"]["archive"],
            "query_bank_sha256": dataset.manifest["sha256"]["query_bank"],
            "git_commit": git_commit(repository_root),
            "target_order_sha256": stable_digest(list(config.target_order)),
            "target_order_index": config.target_order.index(target.target_id),
        },
    )
    adapter = create_adapter(target, config.benchmark.timeout_seconds)
    sampler = _resource_sampler(target, writer)
    writer.append(
        "lifecycle",
        state="PROVISIONED",
        client=client_metadata(),
        target_order=list(config.target_order),
    )
    try:
        if sampler is not None:
            sampler.start()
        connect_start = time.perf_counter_ns()
        connection_attempts = _connect_when_ready(
            adapter,
            writer,
            readiness_seconds=max(120.0, config.benchmark.timeout_seconds * 4),
        )
        writer.append(
            "connection",
            success=True,
            duration_ms=_elapsed_ms(connect_start),
            attempts=connection_attempts,
            engine_version=adapter.version(),
        )
        _measure_fresh_connections(target, config, writer)
        ingest_started = time.perf_counter_ns()
        _timed_phase(writer, "reset", adapter.reset)
        _timed_phase(writer, "schema", adapter.create_schema)
        _load_dataset(config, dataset, adapter, writer)
        writer.append("lifecycle", state="LOADED")
        _validate(config, dataset, adapter, writer)
        _capture_query_plans(dataset, adapter, writer)
        ingest_duration_ms = _elapsed_ms(ingest_started)
        writer.append(
            "ingest_summary",
            duration_ms=ingest_duration_ms,
            nodes=dataset.manifest["counts"]["nodes"],
            relationships=dataset.manifest["counts"]["relationships"],
            nodes_per_second=dataset.manifest["counts"]["nodes"] / (ingest_duration_ms / 1000),
            relationships_per_second=dataset.manifest["counts"]["relationships"]
            / (ingest_duration_ms / 1000),
        )
        writer.append("lifecycle", state="VALIDATED")
        _measure_trivial(config, adapter, writer)
        _measure_reads(config, dataset, adapter, writer)
        _measure_closed_loop(config, dataset, adapter, writer, run_id)
        _measure_open_loop(config, dataset, adapter, writer, run_id)
        final_counts = _unmeasured_with_reconnect(
            adapter, writer, adapter.counts, "post_run_counts"
        )
        final_integrity = _unmeasured_with_reconnect(
            adapter, writer, adapter.integrity, "post_run_integrity"
        )
        expected_counts = _expected_counts(dataset)
        expected_integrity = _expected_integrity(dataset)
        final_passed = final_counts == expected_counts and final_integrity == expected_integrity
        writer.append(
            "post_run_validation",
            passed=final_passed,
            expected_counts=expected_counts,
            actual_counts=final_counts,
            expected_integrity=expected_integrity,
            actual_integrity=final_integrity,
        )
        if not final_passed:
            raise ValueError("Post-run graph validation failed")
        writer.append("lifecycle", state="BENCHMARKED")
    except Exception as error:
        writer.append(
            "run_failure",
            state="FAILED",
            error_type=type(error).__name__,
            error_category=classify_error(error),
        )
        raise
    finally:
        adapter.close()
        if sampler is not None:
            sampler.stop()
    return output_path


def _load_dataset(
    config: AppConfig,
    dataset: PreparedDataset,
    adapter: GraphAdapter,
    writer: ResultWriter,
) -> None:
    users = read_users(dataset.users_path)
    movies = read_movies(dataset.movies_path)
    ratings = read_ratings(dataset.ratings_path)
    batch_size = config.benchmark.batch_size
    for phase, values, loader, unit in (
        ("load_users", users, adapter.load_users, "nodes"),
        ("load_movies", movies, adapter.load_movies, "nodes"),
        ("load_ratings", ratings, adapter.load_ratings, "relationships"),
    ):
        started = time.perf_counter_ns()
        for batch in batched(values, batch_size):
            loader(batch)
        duration_ms = _elapsed_ms(started)
        writer.append(
            "load_phase",
            phase=phase,
            item_kind=unit,
            items=len(values),
            duration_ms=duration_ms,
            items_per_second=len(values) / (duration_ms / 1000),
            batch_size=batch_size,
        )


def _validate(
    config: AppConfig,
    dataset: PreparedDataset,
    adapter: GraphAdapter,
    writer: ResultWriter,
) -> None:
    expected_counts = _expected_counts(dataset)
    actual_counts = adapter.counts()
    counts_passed = actual_counts == expected_counts
    writer.append(
        "validation_counts",
        passed=counts_passed,
        expected=expected_counts,
        actual=actual_counts,
    )
    expected_integrity = _expected_integrity(dataset)
    actual_integrity = adapter.integrity()
    integrity_passed = actual_integrity == expected_integrity
    writer.append(
        "validation_integrity",
        passed=integrity_passed,
        expected=expected_integrity,
        actual=actual_integrity,
    )
    failures: list[dict[str, Any]] = []
    bank = dataset.query_bank
    for entry in bank["traversal_starts"]:
        for workload in ("hop_1", "hop_2", "hop_3"):
            _validate_query(
                adapter,
                writer,
                failures,
                workload,
                int(entry["userId"]),
                entry["expected"][workload],
                bucket=str(entry["bucket"]),
            )
    for entry in bank["point_lookups"]:
        _validate_query(
            adapter,
            writer,
            failures,
            "point_lookup",
            int(entry["movieId"]),
            entry["expected"],
        )
    for entry in bank["filtered_lookups"]:
        _validate_query(
            adapter,
            writer,
            failures,
            "filtered_lookup",
            int(entry["year"]),
            entry["expected"],
        )
    _validate_query(adapter, writer, failures, "aggregation", None, bank["aggregation"]["expected"])
    passed = counts_passed and integrity_passed and not failures
    writer.append("validation_summary", passed=passed, failure_count=len(failures))
    if not passed:
        raise ValueError(f"Correctness validation failed with {len(failures)} query mismatches")


def _validate_query(
    adapter: GraphAdapter,
    writer: ResultWriter,
    failures: list[dict[str, Any]],
    workload: str,
    parameter: int | None,
    expected: dict[str, Any],
    *,
    bucket: str | None = None,
) -> None:
    rows = normalized_rows(adapter.read(workload, parameter))
    actual = {"count": len(rows), "sha256": stable_digest(rows)}
    passed = actual == expected
    writer.append(
        "validation_query",
        workload=workload,
        parameter_id=parameter,
        degree_bucket=bucket,
        passed=passed,
        expected=expected,
        actual=actual,
    )
    if not passed:
        failures.append({"workload": workload, "parameter_id": parameter})


def _measure_trivial(config: AppConfig, adapter: GraphAdapter, writer: ResultWriter) -> None:
    _measure_operation_series(
        config,
        adapter,
        writer,
        workload="return_1",
        parameters=[None],
        operation=lambda _parameter: adapter.trivial_query(),
    )


def _measure_fresh_connections(
    target: TargetConfig,
    config: AppConfig,
    writer: ResultWriter,
) -> None:
    durations: list[float] = []
    error_categories: list[str] = []
    for sequence in range(5):
        probe = create_adapter(target, config.benchmark.timeout_seconds)
        started = time.perf_counter_ns()
        try:
            probe.connect()
            duration_ms = _elapsed_ms(started)
            durations.append(duration_ms)
            writer.append(
                "fresh_connection_sample",
                sequence=sequence,
                success=True,
                duration_ms=duration_ms,
            )
        except Exception as error:
            category = classify_error(error)
            error_categories.append(category)
            writer.append(
                "fresh_connection_sample",
                sequence=sequence,
                success=False,
                duration_ms=_elapsed_ms(started),
                error_type=type(error).__name__,
                error_category=category,
            )
        finally:
            probe.close()
    writer.append(
        "fresh_connection_summary",
        timeouts=error_categories.count("timeout"),
        errors=sum(category != "timeout" for category in error_categories),
        retries=0,
        **summarize(durations, 5),
    )


def _capture_query_plans(
    dataset: PreparedDataset,
    adapter: GraphAdapter,
    writer: ResultWriter,
) -> None:
    bank = dataset.query_bank
    plan_parameters = {
        "point_lookup": int(bank["point_lookups"][0]["movieId"]),
        "filtered_lookup": int(bank["filtered_lookups"][0]["year"]),
        "hop_3": int(bank["traversal_starts"][0]["userId"]),
        "aggregation": None,
    }
    for workload, parameter in plan_parameters.items():
        try:
            plan = adapter.explain(workload, parameter)
            writer.append(
                "query_plan",
                workload=workload,
                parameter_id=parameter,
                success=True,
                plan=plan,
            )
        except Exception as error:
            writer.append(
                "query_plan",
                workload=workload,
                parameter_id=parameter,
                success=False,
                error_type=type(error).__name__,
                error_category=classify_error(error),
            )


def _measure_reads(
    config: AppConfig,
    dataset: PreparedDataset,
    adapter: GraphAdapter,
    writer: ResultWriter,
) -> None:
    bank = dataset.query_bank
    parameter_sets: dict[str, list[int | None]] = {
        "hop_1": [int(entry["userId"]) for entry in bank["traversal_starts"]],
        "hop_2": [int(entry["userId"]) for entry in bank["traversal_starts"]],
        "hop_3": [int(entry["userId"]) for entry in bank["traversal_starts"]],
        "point_lookup": [int(entry["movieId"]) for entry in bank["point_lookups"]],
        "filtered_lookup": [int(entry["year"]) for entry in bank["filtered_lookups"]],
        "aggregation": [None],
    }
    traversal_buckets = {
        int(entry["userId"]): str(entry["bucket"]) for entry in bank["traversal_starts"]
    }
    for workload in READ_WORKLOADS:
        _measure_operation_series(
            config,
            adapter,
            writer,
            workload=workload,
            parameters=parameter_sets[workload],
            operation=lambda parameter, workload=workload: adapter.read(workload, parameter),
            degree_buckets=traversal_buckets if workload.startswith("hop_") else None,
        )


def _measure_operation_series(
    config: AppConfig,
    adapter: GraphAdapter,
    writer: ResultWriter,
    *,
    workload: str,
    parameters: list[int | None],
    operation: Callable[[int | None], list[dict[str, Any]]],
    degree_buckets: dict[int, str] | None = None,
) -> None:
    benchmark = config.benchmark
    warmup_parameters = itertools.cycle(parameters)
    for _ in range(benchmark.warmup_operations):
        operation(next(warmup_parameters))
    for session_number in range(1, benchmark.sessions + 1):
        durations: list[float] = []
        error_categories: list[str] = []
        operation_parameters = itertools.cycle(parameters)
        for sequence in range(benchmark.measured_operations):
            parameter = next(operation_parameters)
            started = time.perf_counter_ns()
            try:
                rows = normalized_rows(operation(parameter))
                duration_ms = _elapsed_ms(started)
                durations.append(duration_ms)
                writer.append(
                    "read_sample",
                    workload=workload,
                    session=session_number,
                    sequence=sequence,
                    parameter_id=parameter,
                    degree_bucket=degree_buckets.get(parameter)
                    if degree_buckets is not None and parameter is not None
                    else None,
                    success=True,
                    duration_ms=duration_ms,
                    result_count=len(rows),
                    result_sha256=stable_digest(rows),
                )
            except Exception as error:
                category = classify_error(error)
                error_categories.append(category)
                writer.append(
                    "read_sample",
                    workload=workload,
                    session=session_number,
                    sequence=sequence,
                    parameter_id=parameter,
                    degree_bucket=degree_buckets.get(parameter)
                    if degree_buckets is not None and parameter is not None
                    else None,
                    success=False,
                    duration_ms=_elapsed_ms(started),
                    error_type=type(error).__name__,
                    error_category=category,
                )
        summary = summarize(durations, benchmark.measured_operations)
        writer.append(
            "read_summary",
            workload=workload,
            session=session_number,
            timeouts=error_categories.count("timeout"),
            errors=sum(category != "timeout" for category in error_categories),
            retries=0,
            **summary,
        )


def _measure_closed_loop(
    config: AppConfig,
    dataset: PreparedDataset,
    adapter: GraphAdapter,
    writer: ResultWriter,
    run_id: str,
) -> None:
    benchmark = config.benchmark
    for mix_name, read_ratio in benchmark.mixes.items():
        for concurrency in benchmark.mixed_concurrency:
            deadline_ns = time.perf_counter_ns() + benchmark.mixed_duration_seconds * 1_000_000_000
            started = time.perf_counter_ns()
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [
                    executor.submit(
                        _closed_loop_worker,
                        adapter,
                        dataset.query_bank,
                        writer,
                        run_id,
                        config.seed + concurrency * 1000 + worker_id,
                        worker_id,
                        read_ratio,
                        deadline_ns,
                    )
                    for worker_id in range(concurrency)
                ]
                worker_results = [future.result() for future in futures]
            duration_seconds = (time.perf_counter_ns() - started) / 1_000_000_000
            outcomes = [outcome for result in worker_results for outcome in result["outcomes"]]
            writer.append(
                "mixed_summary",
                model="closed_loop",
                mix=mix_name,
                read_ratio=read_ratio,
                concurrency=concurrency,
                duration_seconds=duration_seconds,
                achieved_qps=sum(outcome["success"] for outcome in outcomes) / duration_seconds,
                **_summarize_mixed(outcomes),
            )
            _validate_mixed_counts(dataset, adapter, writer, "closed_loop", mix_name, concurrency)


def _closed_loop_worker(
    adapter: GraphAdapter,
    bank: dict[str, Any],
    writer: ResultWriter,
    run_id: str,
    seed: int,
    worker_id: int,
    read_ratio: float,
    deadline_ns: int,
) -> dict[str, Any]:
    randomizer = random.Random(seed)
    sequence = 0
    outcomes: list[dict[str, Any]] = []
    while time.perf_counter_ns() < deadline_ns:
        outcomes.append(
            _mixed_operation(
                adapter, bank, writer, run_id, randomizer, worker_id, sequence, read_ratio, None
            )
        )
        sequence += 1
    return {"outcomes": outcomes}


def _measure_open_loop(
    config: AppConfig,
    dataset: PreparedDataset,
    adapter: GraphAdapter,
    writer: ResultWriter,
    run_id: str,
) -> None:
    benchmark = config.benchmark
    rate = benchmark.open_loop_rate
    duration = benchmark.mixed_duration_seconds
    operation_count = rate * duration
    interval_ns = int(1_000_000_000 / rate)
    max_workers = max(benchmark.mixed_concurrency)
    base_ns = time.perf_counter_ns() + 100_000_000
    futures: list[Future[dict[str, Any]]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for sequence in range(operation_count):
            intended_ns = base_ns + sequence * interval_ns
            remaining_ns = intended_ns - time.perf_counter_ns()
            if remaining_ns > 0:
                time.sleep(remaining_ns / 1_000_000_000)
            futures.append(
                executor.submit(
                    _mixed_operation,
                    adapter,
                    dataset.query_bank,
                    writer,
                    run_id,
                    random.Random(config.seed + sequence),
                    sequence % max_workers,
                    sequence,
                    0.80,
                    intended_ns,
                )
            )
        outcomes = [future.result() for future in as_completed(futures)]
    elapsed_seconds = (time.perf_counter_ns() - base_ns) / 1_000_000_000
    writer.append(
        "mixed_summary",
        model="open_loop",
        mix="mixed",
        read_ratio=0.80,
        concurrency=max_workers,
        offered_qps=rate,
        duration_seconds=elapsed_seconds,
        achieved_qps=sum(outcome["success"] for outcome in outcomes) / elapsed_seconds,
        **_summarize_mixed(outcomes),
    )
    _validate_mixed_counts(dataset, adapter, writer, "open_loop", "mixed", max_workers)


def _mixed_operation(
    adapter: GraphAdapter,
    bank: dict[str, Any],
    writer: ResultWriter,
    run_id: str,
    randomizer: random.Random,
    worker_id: int,
    sequence: int,
    read_ratio: float,
    intended_ns: int | None,
) -> dict[str, Any]:
    is_read = randomizer.random() < read_ratio
    if is_read:
        workload = randomizer.choice(("point_lookup", "hop_1", "hop_2"))
        if workload == "point_lookup":
            parameter = int(randomizer.choice(bank["point_lookups"])["movieId"])
        else:
            parameter = int(randomizer.choice(bank["traversal_starts"])["userId"])

        def operation() -> list[dict[str, Any]]:
            return adapter.read(workload, parameter)
    else:
        workload = "steady_write"
        parameter = int(randomizer.choice(bank["traversal_starts"])["userId"])
        token = stable_digest([run_id, worker_id, sequence])[:16]

        def operation() -> list[dict[str, Any]]:
            return adapter.write_token(parameter, token)

    started = time.perf_counter_ns()
    latency_origin = intended_ns if intended_ns is not None else started
    try:
        rows = operation()
        finished = time.perf_counter_ns()
        service_ms = (finished - started) / 1_000_000
        latency_ms = (finished - latency_origin) / 1_000_000
        writer.append(
            "mixed_sample",
            model="open_loop" if intended_ns is not None else "closed_loop",
            worker_id=worker_id,
            sequence=sequence,
            workload=workload,
            parameter_id=parameter,
            success=True,
            service_ms=service_ms,
            latency_ms=latency_ms,
            result_count=len(rows),
        )
        return {
            "success": True,
            "operation_kind": "read" if is_read else "write",
            "latency_ms": latency_ms,
            "service_ms": service_ms,
            "error_category": None,
        }
    except Exception as error:
        finished = time.perf_counter_ns()
        service_ms = (finished - started) / 1_000_000
        latency_ms = (finished - latency_origin) / 1_000_000
        category = classify_error(error)
        writer.append(
            "mixed_sample",
            model="open_loop" if intended_ns is not None else "closed_loop",
            worker_id=worker_id,
            sequence=sequence,
            workload=workload,
            parameter_id=parameter,
            success=False,
            service_ms=service_ms,
            latency_ms=latency_ms,
            error_type=type(error).__name__,
            error_category=category,
        )
        return {
            "success": False,
            "operation_kind": "read" if is_read else "write",
            "latency_ms": latency_ms,
            "service_ms": service_ms,
            "error_category": category,
        }


def _summarize_mixed(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    successful_latencies = [
        float(outcome["latency_ms"]) for outcome in outcomes if outcome["success"]
    ]
    summary = summarize(successful_latencies, len(outcomes))
    return {
        **summary,
        "read_attempts": sum(outcome["operation_kind"] == "read" for outcome in outcomes),
        "write_attempts": sum(outcome["operation_kind"] == "write" for outcome in outcomes),
        "timeouts": sum(outcome["error_category"] == "timeout" for outcome in outcomes),
        "errors": sum(
            not outcome["success"] and outcome["error_category"] != "timeout"
            for outcome in outcomes
        ),
        "retries": 0,
        "reconnects": 0,
    }


def _validate_mixed_counts(
    dataset: PreparedDataset,
    adapter: GraphAdapter,
    writer: ResultWriter,
    model: str,
    mix: str,
    concurrency: int,
) -> None:
    expected = _expected_counts(dataset)
    actual = _unmeasured_with_reconnect(
        adapter,
        writer,
        adapter.counts,
        f"{model}_{mix}_{concurrency}_counts",
    )
    passed = actual == expected
    writer.append(
        "mixed_count_validation",
        model=model,
        mix=mix,
        concurrency=concurrency,
        passed=passed,
        expected=expected,
        actual=actual,
    )
    if not passed:
        raise ValueError(f"Graph counts changed during {model} {mix} at concurrency {concurrency}")


def _unmeasured_with_reconnect(
    adapter: GraphAdapter,
    writer: ResultWriter,
    operation: Callable[[], Any],
    phase: str,
) -> Any:
    try:
        return operation()
    except Exception as error:
        if classify_error(error) != "connection":
            raise
        adapter.close()
        attempts = _connect_when_ready(adapter, writer, readiness_seconds=120.0)
        writer.append(
            "validation_reconnect",
            phase=phase,
            attempts=attempts,
            triggering_error_type=type(error).__name__,
            triggering_error_category="connection",
        )
        return operation()


def _expected_counts(dataset: PreparedDataset) -> dict[str, int]:
    return {
        "users": int(dataset.manifest["counts"]["users"]),
        "movies": int(dataset.manifest["counts"]["movies"]),
        "relationships": int(dataset.manifest["counts"]["relationships"]),
    }


def _expected_integrity(dataset: PreparedDataset) -> dict[str, int]:
    source_integrity = dataset.manifest["integrity"]
    return {
        "unique_user_ids": int(source_integrity["unique_user_ids"]),
        "unique_movie_ids": int(source_integrity["unique_movie_ids"]),
        "duplicate_rating_edge_keys": int(source_integrity["duplicate_rating_edge_keys"]),
        "invalid_relationship_endpoints": int(source_integrity["invalid_relationship_endpoints"]),
        "rating_tenths_sum": int(source_integrity["rating"]["tenths_sum"]),
        "timestamp_min": int(source_integrity["timestamp"]["min"]),
        "timestamp_max": int(source_integrity["timestamp"]["max"]),
        "timestamp_sum": int(source_integrity["timestamp"]["sum"]),
        "movie_year_null_count": int(source_integrity["movie_year"]["null_count"]),
    }


def _timed_phase(writer: ResultWriter, phase: str, operation: Callable[[], None]) -> None:
    started = time.perf_counter_ns()
    operation()
    writer.append("phase", phase=phase, success=True, duration_ms=_elapsed_ms(started))


def _connect_when_ready(
    adapter: GraphAdapter,
    writer: ResultWriter,
    *,
    readiness_seconds: float,
) -> int:
    deadline = time.perf_counter() + readiness_seconds
    attempts = 0
    while True:
        attempts += 1
        started = time.perf_counter_ns()
        try:
            adapter.connect()
            writer.append(
                "connection_attempt",
                attempt=attempts,
                success=True,
                duration_ms=_elapsed_ms(started),
            )
            return attempts
        except Exception as error:
            adapter.close()
            writer.append(
                "connection_attempt",
                attempt=attempts,
                success=False,
                duration_ms=_elapsed_ms(started),
                error_type=type(error).__name__,
                error_category=classify_error(error),
            )
            if time.perf_counter() >= deadline:
                raise
            time.sleep(1)


def _elapsed_ms(started_ns: int) -> float:
    return (time.perf_counter_ns() - started_ns) / 1_000_000


def _run_id(label: str, target_id: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{label}-{target_id}-{uuid.uuid4().hex[:8]}"


def _resource_sampler(target: TargetConfig, writer: ResultWriter) -> ResourceSampler | None:
    if target.deployment != "controlled-local":
        return None
    required = ("container_name", "data_directory", "storage_mount")
    missing = [key for key in required if not target.settings.get(key)]
    if missing:
        raise ValueError(f"Controlled target {target.target_id} lacks resource fields: {missing}")
    return ResourceSampler(
        writer,
        container_name=str(target.settings["container_name"]),
        data_directory=str(target.settings["data_directory"]),
        storage_mount=str(target.settings["storage_mount"]),
    )
