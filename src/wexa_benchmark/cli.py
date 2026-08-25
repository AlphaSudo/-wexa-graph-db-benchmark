from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import create_adapter
from .audit import audit_results
from .config import AppConfig, load_config
from .dataset import load_prepared_dataset, prepare_dataset
from .doctor import run_doctor
from .package import package_results
from .report import generate_report
from .runner import run_target
from .util import load_dotenv


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    load_dotenv(repository_root / ".env")
    config = load_config((repository_root / args.config).resolve())

    try:
        if args.command == "prepare":
            prepared = prepare_dataset(config.dataset, config.seed, repository_root)
            print(json.dumps(prepared.manifest, indent=2, sort_keys=True))
            return 0
        if args.command == "doctor":
            result = run_doctor(config, repository_root, offline=args.offline)
            if args.target:
                target = _target(config, args.target)
                adapter = create_adapter(target, config.benchmark.timeout_seconds)
                try:
                    adapter.connect()
                    result["database"] = {
                        "target": target.target_id,
                        "passed": True,
                        "version": adapter.version(),
                    }
                finally:
                    adapter.close()
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["passed"] else 1
        if args.command == "run":
            target = _target(config, args.target)
            prepared = load_prepared_dataset(repository_root)
            output = run_target(config, target, prepared, repository_root)
            print(json.dumps({"completed": True, "result_file": str(output)}, indent=2))
            return 0
        if args.command == "audit":
            result = audit_results(config, repository_root)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["passed"] else 1
        if args.command == "report":
            json_path, markdown_path = generate_report(config, repository_root)
            print(json.dumps({"json": str(json_path), "markdown": str(markdown_path)}, indent=2))
            return 0
        if args.command == "package":
            print(json.dumps(package_results(config, repository_root), indent=2, sort_keys=True))
            return 0
    except (FileNotFoundError, KeyError, RuntimeError, ValueError) as error:
        print(f"ERROR [{type(error).__name__}]: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        print(
            f"ERROR [{type(error).__name__}]: command failed; inspect the append-only raw run",
            file=sys.stderr,
        )
        return 3
    parser.error(f"Unknown command: {args.command}")
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wexa-bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Download, normalize, and checksum MovieLens")
    _config_argument(prepare)

    doctor = subparsers.add_parser(
        "doctor", help="Check local tools and optional target connectivity"
    )
    _config_argument(doctor)
    doctor.add_argument("--offline", action="store_true", help="Never connect to a database")
    doctor.add_argument("--target", help="Target ID to verify; omitted in offline preflight")

    run = subparsers.add_parser("run", help="Load, validate, and benchmark one target")
    _config_argument(run)
    run.add_argument("--target", required=True, help="Exact target ID from the config")

    audit = subparsers.add_parser("audit", help="Fail if required result evidence is missing")
    _config_argument(audit)

    report = subparsers.add_parser("report", help="Generate tables from matching raw results")
    _config_argument(report)
    package = subparsers.add_parser(
        "package", help="Deterministically gzip matching raw JSONL without deleting it"
    )
    _config_argument(package)
    return parser


def _config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config", default="configs/official.yaml", help="Config path from repo root"
    )


def _target(config: AppConfig, target_id: str):
    try:
        target = config.targets[target_id]
    except KeyError as error:
        choices = sorted(config.targets)
        raise ValueError(f"Unknown target {target_id!r}; choose from {choices}") from error
    if not target.enabled:
        raise ValueError(f"Target {target_id!r} is disabled")
    return target


if __name__ == "__main__":
    raise SystemExit(main())
