from __future__ import annotations

import math
import random
import statistics
from typing import Any


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile of an empty sequence")
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be in [0, 1]")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize(durations_ms: list[float], attempts: int) -> dict[str, Any]:
    failures = attempts - len(durations_ms)
    if not durations_ms:
        return {
            "attempts": attempts,
            "successes": 0,
            "failures": failures,
            "success_rate": 0.0,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "min_ms": None,
            "max_ms": None,
            "mad_ms": None,
            "cv": None,
            "p50_ci95_low_ms": None,
            "p50_ci95_high_ms": None,
        }
    median = statistics.median(durations_ms)
    mad = statistics.median(abs(value - median) for value in durations_ms)
    mean = statistics.fmean(durations_ms)
    cv = statistics.pstdev(durations_ms) / mean if mean else None
    ci_low, ci_high = _bootstrap_median_ci(durations_ms)
    return {
        "attempts": attempts,
        "successes": len(durations_ms),
        "failures": failures,
        "success_rate": len(durations_ms) / attempts if attempts else 0.0,
        "p50_ms": percentile(durations_ms, 0.50),
        "p95_ms": percentile(durations_ms, 0.95),
        "p99_ms": percentile(durations_ms, 0.99),
        "min_ms": min(durations_ms),
        "max_ms": max(durations_ms),
        "mad_ms": mad,
        "cv": cv,
        "p50_ci95_low_ms": ci_low,
        "p50_ci95_high_ms": ci_high,
    }


def _bootstrap_median_ci(values: list[float], resamples: int = 1000) -> tuple[float, float]:
    if len(values) == 1:
        return values[0], values[0]
    randomizer = random.Random(20260825 + len(values))
    medians = [
        statistics.median(randomizer.choices(values, k=len(values))) for _ in range(resamples)
    ]
    return percentile(medians, 0.025), percentile(medians, 0.975)
