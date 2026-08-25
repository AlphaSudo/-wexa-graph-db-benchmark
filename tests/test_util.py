from pathlib import Path

import pytest

from wexa_benchmark.results import ResultWriter, read_records
from wexa_benchmark.util import normalized_rows, stable_digest


def test_normalized_rows_are_order_independent() -> None:
    first = normalized_rows([{"id": 2}, {"id": 1}])
    second = normalized_rows([{"id": 1}, {"id": 2}])
    assert stable_digest(first) == stable_digest(second)


def test_writer_creates_append_only_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    writer = ResultWriter(path, {"run_id": "example"})
    writer.append("sample", success=True)
    assert read_records(path)[0]["success"] is True
    with pytest.raises(FileExistsError):
        ResultWriter(path, {"run_id": "other"})


def test_writer_rejects_secret_bearing_fields(tmp_path: Path) -> None:
    writer = ResultWriter(tmp_path / "run.jsonl", {"run_id": "example"})
    with pytest.raises(ValueError):
        writer.append("sample", password="should-not-be-written")
