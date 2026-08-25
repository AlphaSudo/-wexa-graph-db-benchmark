from __future__ import annotations

from ..config import TargetConfig
from ..util import require_env
from .arangodb import ArangoAdapter
from .base import GraphAdapter
from .cypher import CypherAdapter
from .falkordb import FalkorAdapter


def create_adapter(target: TargetConfig, timeout_seconds: float) -> GraphAdapter:
    settings = target.settings
    if target.adapter == "cypher":
        username = _optional_env(settings, "username")
        password = _optional_env(settings, "password")
        return CypherAdapter(
            target.target_id,
            timeout_seconds,
            uri=_required_env(settings, "uri"),
            username=username,
            password=password,
            database=_optional_string(settings.get("database")),
            dialect=str(settings.get("dialect", "neo4j")),
        )
    if target.adapter == "falkordb":
        return FalkorAdapter(
            target.target_id,
            timeout_seconds,
            host=_required_env(settings, "host"),
            port=int(_required_env(settings, "port")),
            password=_optional_env(settings, "password"),
            graph_name=str(settings.get("graph", "movielens")),
        )
    if target.adapter == "arangodb":
        return ArangoAdapter(
            target.target_id,
            timeout_seconds,
            url=_required_env(settings, "url"),
            username=_optional_env(settings, "username"),
            password=_optional_env(settings, "password"),
            database=str(settings.get("database", "movielens")),
        )
    raise ValueError(f"Unsupported adapter type: {target.adapter}")


def _required_env(settings: dict[str, object], prefix: str) -> str:
    return require_env(
        str(settings[f"{prefix}_env"]),
        default=_optional_string(settings.get(f"{prefix}_default")),
    )


def _optional_env(settings: dict[str, object], prefix: str) -> str | None:
    name = settings.get(f"{prefix}_env")
    if name is None:
        return None
    return require_env(
        str(name),
        default=_optional_string(settings.get(f"{prefix}_default")),
    )


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)
