from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")

SECRET_KEY_PATTERN = re.compile(r"(password|secret|token|credential|uri)$", re.IGNORECASE)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def batched(values: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    if size < 1:
        raise ValueError("batch size must be positive")
    for start in range(0, len(values), size):
        yield values[start : start + size]


def normalized_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized = [{key: normalize_scalar(value) for key, value in row.items()} for row in rows]
    return sorted(normalized, key=canonical_json)


def normalize_scalar(value: Any) -> Any:
    if isinstance(value, float):
        return float(f"{value:.12g}")
    if isinstance(value, Mapping):
        return {str(k): normalize_scalar(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_scalar(item) for item in value]
    return value


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name: str, *, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip() or "REPLACE_ME" in value:
        raise ValueError(f"Required environment variable {name} is missing or still a placeholder")
    return value


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if SECRET_KEY_PATTERN.search(str(key)):
            result[str(key)] = "<redacted>"
        elif isinstance(item, Mapping):
            result[str(key)] = redact_mapping(item)
        elif isinstance(item, list):
            result[str(key)] = [
                redact_mapping(child) if isinstance(child, Mapping) else child for child in item
            ]
        else:
            result[str(key)] = item
    return result


def client_metadata() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
    }


def git_commit(repository_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "uncommitted"
    return completed.stdout.strip()


def classify_error(error: BaseException) -> str:
    name = type(error).__name__.lower()
    if "timeout" in name:
        return "timeout"
    if "auth" in name or "credential" in name:
        return "authentication"
    if "connect" in name or "serviceunavailable" in name:
        return "connection"
    if "memory" in name or "oom" in name:
        return "out_of_memory"
    return "server_or_client"
