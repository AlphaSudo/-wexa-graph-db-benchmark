import pytest

from wexa_benchmark.stats import percentile, summarize


def test_percentile_uses_linear_interpolation() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    assert percentile(values, 0.5) == 2.5
    assert percentile(values, 0.95) == pytest.approx(3.85)


def test_summary_keeps_failures_visible() -> None:
    result = summarize([1.0, 2.0, 3.0], attempts=5)
    assert result["successes"] == 3
    assert result["failures"] == 2
    assert result["success_rate"] == 0.6


def test_empty_summary_is_explicit() -> None:
    result = summarize([], attempts=4)
    assert result["p50_ms"] is None
    assert result["failures"] == 4
