from __future__ import annotations

import os
import subprocess
import threading
from typing import Any

from .results import ResultWriter
from .stats import percentile

STATS_TEMPLATE = (
    "{{.ID}}|{{.Name}}|{{.CPU}}|{{.AvgCPU}}|{{.MemUsage}}|{{.MemPerc}}|"
    "{{.NetIO}}|{{.BlockIO}}|{{.PIDS}}"
)


class ResourceSampler:
    """Capture a one-second Podman stats stream without per-sample process startup."""

    def __init__(
        self,
        writer: ResultWriter,
        *,
        container_name: str,
        data_directory: str,
        storage_mount: str,
    ) -> None:
        self._writer = writer
        self._container_name = container_name
        self._data_directory = data_directory
        self._storage_mount = storage_mount
        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._samples: list[dict[str, Any]] = []
        self._error: str | None = None

    def start(self) -> None:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self._process = subprocess.Popen(
            [
                "podman",
                "stats",
                "--no-reset",
                "--interval",
                "1",
                "--format",
                STATS_TEMPLATE,
                self._container_name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=creation_flags,
        )
        self._thread = threading.Thread(target=self._read_stream, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=8) or not self._samples:
            self.stop()
            detail = f": {self._error}" if self._error else ""
            raise RuntimeError(f"Resource sampler produced no startup sample{detail}")

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        if self._thread is not None:
            self._thread.join(timeout=5)
        if not self._samples:
            return
        disk = _disk_snapshot(
            self._container_name,
            self._data_directory,
            self._storage_mount,
        )
        cpu = [float(sample["cpu_percent"]) for sample in self._samples]
        memory = [int(sample["memory_usage_bytes"]) for sample in self._samples]
        self._writer.append(
            "resource_summary",
            passed=disk.get("passed", False),
            sample_interval_seconds=1,
            samples=len(self._samples),
            cpu_percent_p50=percentile(cpu, 0.50),
            cpu_percent_p95=percentile(cpu, 0.95),
            cpu_percent_max=max(cpu),
            memory_bytes_p50=percentile([float(value) for value in memory], 0.50),
            memory_bytes_p95=percentile([float(value) for value in memory], 0.95),
            memory_bytes_peak=max(memory),
            disk=disk,
            sampler_error=self._error,
        )

    def _read_stream(self) -> None:
        try:
            if self._process is None or self._process.stdout is None:
                raise RuntimeError("Resource sampler process was not initialized")
            for line in self._process.stdout:
                if not line.strip():
                    continue
                sample = parse_stats_line(line)
                self._samples.append(sample)
                self._writer.append("resource_sample", **sample)
                self._ready.set()
        except Exception as error:
            self._error = f"{type(error).__name__}: {error}"
        finally:
            self._ready.set()


def parse_stats_line(line: str) -> dict[str, Any]:
    values = line.strip().split("|")
    if len(values) != 9:
        raise ValueError(f"Expected 9 Podman stats fields, found {len(values)}")
    memory_used, memory_limit = _pair(values[4])
    network_input, network_output = _pair(values[6])
    block_input, block_output = _pair(values[7])
    return {
        "container_id": values[0],
        "container_name": values[1],
        "cpu_percent": float(values[2].rstrip("%")),
        "average_cpu_percent": float(values[3].rstrip("%")),
        "memory_usage_bytes": parse_size(memory_used),
        "memory_limit_bytes": parse_size(memory_limit),
        "memory_percent": float(values[5].rstrip("%")),
        "network_input_bytes": parse_size(network_input),
        "network_output_bytes": parse_size(network_output),
        "block_input_bytes": parse_size(block_input),
        "block_output_bytes": parse_size(block_output),
        "pids": int(values[8]),
    }


def parse_size(value: str) -> int:
    compact = value.strip().replace(" ", "")
    units = {
        "B": 1,
        "kB": 1000,
        "MB": 1000**2,
        "GB": 1000**3,
        "KiB": 1024,
        "MiB": 1024**2,
        "GiB": 1024**3,
    }
    for unit in sorted(units, key=len, reverse=True):
        if compact.endswith(unit):
            return round(float(compact[: -len(unit)]) * units[unit])
    raise ValueError(f"Unsupported size value: {value!r}")


def _pair(value: str) -> tuple[str, str]:
    parts = [part.strip() for part in value.split("/")]
    if len(parts) != 2:
        raise ValueError(f"Expected a usage/limit pair, found: {value!r}")
    return parts[0], parts[1]


def _disk_snapshot(container_name: str, data_directory: str, storage_mount: str) -> dict[str, Any]:
    try:
        filesystem = (
            subprocess.run(
                ["podman", "exec", container_name, "df", "-B1", data_directory],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=15,
            )
            .stdout.strip()
            .splitlines()
        )
        if len(filesystem) < 2:
            raise ValueError("df returned no filesystem data")
        columns = filesystem[-1].split()
        if len(columns) < 6:
            raise ValueError(f"Unexpected df row: {filesystem[-1]!r}")
        usage = subprocess.run(
            ["podman", "machine", "ssh", "--", "sudo", "du", "-sb", storage_mount],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
        ).stdout.strip()
        return {
            "passed": True,
            "filesystem": columns[0],
            "capacity_bytes": int(columns[1]),
            "used_bytes": int(columns[2]),
            "available_bytes": int(columns[3]),
            "mounted_on": columns[-1],
            "data_directory_bytes": int(usage.split()[0]),
        }
    except Exception as error:
        return {"passed": False, "error_type": type(error).__name__}
