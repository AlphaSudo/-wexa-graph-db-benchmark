from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

from .config import AppConfig


def run_doctor(config: AppConfig, repository_root: Path, *, offline: bool) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "python": {
            "value": platform.python_version(),
            "passed": (3, 11) <= sys.version_info[:2] < (3, 14),
        },
        "config": {"value": str(config.path), "passed": config.path.exists()},
        "repository": {"value": str(repository_root), "passed": repository_root.exists()},
        "podman": {"value": shutil.which("podman"), "passed": shutil.which("podman") is not None},
        "git": {"value": shutil.which("git"), "passed": shutil.which("git") is not None},
    }
    environment: dict[str, bool] = {}
    for target in config.targets.values():
        for key, value in target.settings.items():
            if key.endswith("_env"):
                environment[str(value)] = bool(os.getenv(str(value)))
    checks["environment_names"] = environment
    if offline:
        checks["mode"] = "offline: no database connection attempted"
    checks["passed"] = all(
        item.get("passed", True) for item in checks.values() if isinstance(item, dict)
    )
    return checks
