from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .util import sha256_file


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    url: str
    expected_users: int
    expected_movies: int
    expected_relationships: int
    query_starts_per_bucket: int


@dataclass(frozen=True)
class BenchmarkConfig:
    batch_size: int
    warmup_operations: int
    measured_operations: int
    sessions: int
    timeout_seconds: float
    mixed_duration_seconds: int
    mixed_concurrency: tuple[int, ...]
    mixes: dict[str, float]
    open_loop_rate: int
    minimum_success_rate: float


@dataclass(frozen=True)
class TargetConfig:
    target_id: str
    adapter: str
    deployment: str
    enabled: bool
    settings: dict[str, Any]


@dataclass(frozen=True)
class AppConfig:
    path: Path
    schema_version: int
    run_label: str
    seed: int
    target_order: tuple[str, ...]
    dataset: DatasetConfig
    benchmark: BenchmarkConfig
    targets: dict[str, TargetConfig]
    sha256: str


def load_config(path: Path) -> AppConfig:
    resolved = path.resolve()
    raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a mapping")
    if raw.get("schema_version") != 1:
        raise ValueError("Only config schema_version 1 is supported")

    dataset_raw = _mapping(raw, "dataset")
    benchmark_raw = _mapping(raw, "benchmark")
    target_raw = _mapping(raw, "targets")

    dataset = DatasetConfig(
        name=str(dataset_raw["name"]),
        url=str(dataset_raw["url"]),
        expected_users=int(dataset_raw["expected_users"]),
        expected_movies=int(dataset_raw["expected_movies"]),
        expected_relationships=int(dataset_raw["expected_relationships"]),
        query_starts_per_bucket=int(dataset_raw["query_starts_per_bucket"]),
    )
    benchmark = BenchmarkConfig(
        batch_size=int(benchmark_raw["batch_size"]),
        warmup_operations=int(benchmark_raw["warmup_operations"]),
        measured_operations=int(benchmark_raw["measured_operations"]),
        sessions=int(benchmark_raw["sessions"]),
        timeout_seconds=float(benchmark_raw["timeout_seconds"]),
        mixed_duration_seconds=int(benchmark_raw["mixed_duration_seconds"]),
        mixed_concurrency=tuple(int(item) for item in benchmark_raw["mixed_concurrency"]),
        mixes={str(key): float(value) for key, value in _mapping(benchmark_raw, "mixes").items()},
        open_loop_rate=int(benchmark_raw["open_loop_rate"]),
        minimum_success_rate=float(benchmark_raw["minimum_success_rate"]),
    )
    targets = {
        str(target_id): TargetConfig(
            target_id=str(target_id),
            adapter=str(settings["adapter"]),
            deployment=str(settings["deployment"]),
            enabled=bool(settings.get("enabled", True)),
            settings={
                str(key): value
                for key, value in settings.items()
                if key not in {"adapter", "deployment", "enabled"}
            },
        )
        for target_id, settings in target_raw.items()
    }
    config = AppConfig(
        path=resolved,
        schema_version=1,
        run_label=str(raw["run_label"]),
        seed=int(raw["seed"]),
        target_order=tuple(str(value) for value in raw.get("target_order", targets)),
        dataset=dataset,
        benchmark=benchmark,
        targets=targets,
        sha256=sha256_file(resolved),
    )
    _validate(config)
    return config


def _mapping(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping")
    return value


def _validate(config: AppConfig) -> None:
    benchmark = config.benchmark
    if benchmark.batch_size < 1 or benchmark.measured_operations < 1:
        raise ValueError("Batch size and measured operations must be positive")
    if not 0 < benchmark.minimum_success_rate <= 1:
        raise ValueError("minimum_success_rate must be in (0, 1]")
    if any(not 0 <= read_ratio <= 1 for read_ratio in benchmark.mixes.values()):
        raise ValueError("Every mix ratio must be in [0, 1]")
    enabled_targets = {target_id for target_id, target in config.targets.items() if target.enabled}
    if len(config.target_order) != len(set(config.target_order)):
        raise ValueError("target_order must not contain duplicates")
    if set(config.target_order) != enabled_targets:
        raise ValueError("target_order must contain every enabled target exactly once")
    if config.run_label == "official":
        if benchmark.measured_operations < 100:
            raise ValueError("Official config requires at least 100 measured read operations")
        if benchmark.sessions < 3:
            raise ValueError("Official config requires at least three independent sessions")
        if config.dataset.query_starts_per_bucket < 25:
            raise ValueError("Official config requires 25 traversal starts per degree bucket")
