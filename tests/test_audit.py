import json
from pathlib import Path

from wexa_benchmark.audit import audit_results
from wexa_benchmark.config import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_audit_rejects_missing_enabled_targets(tmp_path: Path) -> None:
    config = load_config(ROOT / "configs" / "smoke.yaml")
    (tmp_path / "results" / "raw").mkdir(parents=True)
    result = audit_results(config, tmp_path)
    assert result["passed"] is False
    assert len(result["issues"]) == len(config.targets)


def test_audit_rejects_stale_config_and_query_bank(tmp_path: Path) -> None:
    config = load_config(ROOT / "configs" / "smoke.yaml")
    raw_root = tmp_path / "results" / "raw"
    raw_root.mkdir(parents=True)
    data_root = tmp_path / "data"
    data_root.mkdir()
    (data_root / "query_bank.json").write_text("{}\n", encoding="utf-8")
    target_id = next(iter(config.targets))
    records = [
        {
            "target_id": target_id,
            "config_sha256": "stale",
            "query_bank_sha256": "stale",
            "record_type": "lifecycle",
            "state": "BENCHMARKED",
        }
    ]
    (raw_root / "run.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    result = audit_results(config, tmp_path)
    assert any("stale config" in issue for issue in result["issues"])
    assert any("stale query bank" in issue for issue in result["issues"])
