from __future__ import annotations

import gzip
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .util import canonical_json


class ResultWriter:
    """Thread-safe append-only JSONL writer for one immutable run."""

    def __init__(self, path: Path, base_record: dict[str, Any]) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise FileExistsError(f"Refusing to overwrite existing run artifact: {self.path}")
        self._base = dict(base_record)
        self._lock = threading.Lock()

    def append(self, record_type: str, **fields: Any) -> None:
        record = {
            **self._base,
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "record_type": record_type,
            **fields,
        }
        serialized = canonical_json(record)
        _guard_serialized_record(serialized)
        with self._lock, self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized + "\n")
            stream.flush()


def read_records(path: Path) -> list[dict[str, Any]]:
    records = []
    with _open_text(path) as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from error
    return records


def read_result_text(path: Path) -> str:
    with _open_text(path) as stream:
        return stream.read()


def read_first_record(path: Path) -> dict[str, Any] | None:
    with _open_text(path) as stream:
        for line in stream:
            if line.strip():
                return json.loads(line)
    return None


def result_paths(raw_root: Path) -> list[Path]:
    choices: dict[str, Path] = {}
    for path in sorted((*raw_root.glob("*.jsonl.gz"), *raw_root.glob("*.jsonl"))):
        key = path.name.removesuffix(".gz")
        if key not in choices or path.suffix == ".jsonl":
            choices[key] = path
    return [choices[key] for key in sorted(choices)]


def _open_text(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, mode="rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def _guard_serialized_record(serialized: str) -> None:
    forbidden = ("bolt+s://", "neo4j+s://", '"password":', '"credential":')
    lowered = serialized.lower()
    matches = [token for token in forbidden if token in lowered]
    if matches:
        raise ValueError(f"Refusing to write secret-bearing result fields: {matches}")
