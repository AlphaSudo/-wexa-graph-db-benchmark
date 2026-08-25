from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


class GraphAdapter(ABC):
    """Logical database contract shared by all benchmark targets."""

    def __init__(self, target_id: str, timeout_seconds: float) -> None:
        self.target_id = target_id
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def connect(self) -> None:
        """Open the client and verify connectivity."""

    @abstractmethod
    def close(self) -> None:
        """Release client resources."""

    @abstractmethod
    def reset(self) -> None:
        """Remove benchmark data without changing the configured resource tier."""

    @abstractmethod
    def create_schema(self) -> None:
        """Create the equivalent logical indexes and constraints."""

    @abstractmethod
    def load_users(self, rows: Sequence[dict[str, Any]]) -> None:
        """Load one user batch."""

    @abstractmethod
    def load_movies(self, rows: Sequence[dict[str, Any]]) -> None:
        """Load one movie batch."""

    @abstractmethod
    def load_ratings(self, rows: Sequence[dict[str, Any]]) -> None:
        """Load one rating batch."""

    @abstractmethod
    def counts(self) -> dict[str, int]:
        """Return graph counts used by the correctness gate."""

    @abstractmethod
    def integrity(self) -> dict[str, int]:
        """Return deterministic structural and property aggregates."""

    @abstractmethod
    def explain(self, workload: str, parameter: int | None = None) -> dict[str, Any]:
        """Return an unmeasured logical execution plan where supported."""

    @abstractmethod
    def read(self, workload: str, parameter: int | None = None) -> list[dict[str, Any]]:
        """Run and fully consume one logical read workload."""

    @abstractmethod
    def write_token(self, user_id: int, token: str) -> list[dict[str, Any]]:
        """Run the steady-state write without growing the graph."""

    @abstractmethod
    def trivial_query(self) -> list[dict[str, Any]]:
        """Run a pooled protocol-floor query."""

    @abstractmethod
    def version(self) -> str:
        """Return the live engine version where observable."""
