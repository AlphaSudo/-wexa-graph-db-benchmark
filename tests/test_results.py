import gzip
from pathlib import Path

from wexa_benchmark.results import read_records, result_paths


def test_read_records_supports_gzip_and_deduplicates_local_twins(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    plain = raw / "run.jsonl"
    compressed = raw / "run.jsonl.gz"
    plain.write_text('{"value":1}\n', encoding="utf-8")
    with gzip.open(compressed, mode="wt", encoding="utf-8") as stream:
        stream.write('{"value":1}\n')
    assert result_paths(raw) == [plain]
    plain.unlink()
    assert result_paths(raw) == [compressed]
    assert read_records(compressed) == [{"value": 1}]
