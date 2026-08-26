from __future__ import annotations

import gzip
import hashlib
import shutil
from pathlib import Path
from typing import Any

from .config import AppConfig
from .results import read_first_record, result_paths
from .util import sha256_file


def package_results(config: AppConfig, repository_root: Path) -> dict[str, Any]:
    raw_root = repository_root / "results" / "raw"
    packaged: list[dict[str, Any]] = []
    for source in result_paths(raw_root):
        if source.name.endswith(".gz"):
            continue
        first = read_first_record(source)
        if not first or first.get("config_sha256") != config.sha256:
            continue
        destination = source.with_suffix(source.suffix + ".gz")
        if destination.exists():
            with gzip.open(destination, "rb") as archived:
                archived_source_sha256 = _sha256_stream(archived)
            if archived_source_sha256 != sha256_file(source):
                raise FileExistsError(f"Existing package does not match its source: {destination}")
            continue
        with (
            source.open("rb") as input_stream,
            destination.open("wb") as output_stream,
            gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=output_stream,
                mtime=0,
                compresslevel=9,
            ) as compressed,
        ):
            shutil.copyfileobj(input_stream, compressed, length=1024 * 1024)
        packaged.append(
            {
                "source": source.name,
                "destination": destination.name,
                "source_bytes": source.stat().st_size,
                "compressed_bytes": destination.stat().st_size,
                "sha256": sha256_file(destination),
            }
        )
    return {"config_sha256": config.sha256, "packaged": packaged}


def _sha256_stream(stream: Any) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()
