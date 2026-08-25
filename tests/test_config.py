from pathlib import Path

from wexa_benchmark.config import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_official_config_enforces_required_sample_floor() -> None:
    config = load_config(ROOT / "configs" / "official.yaml")
    assert config.benchmark.measured_operations >= 100
    assert config.benchmark.sessions >= 3
    assert config.dataset.query_starts_per_bucket >= 25
    assert len(config.targets) >= 5
    assert set(config.target_order) == set(config.targets)


def test_smoke_config_is_fast_but_has_all_local_adapters() -> None:
    config = load_config(ROOT / "configs" / "smoke.yaml")
    assert config.run_label == "smoke"
    assert {target.adapter for target in config.targets.values()} == {
        "cypher",
        "falkordb",
        "arangodb",
    }
