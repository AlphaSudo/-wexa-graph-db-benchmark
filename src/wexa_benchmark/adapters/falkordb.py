from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from falkordb import FalkorDB

from .base import GraphAdapter
from .cypher import INTEGRITY_QUERIES, READ_QUERIES


class FalkorAdapter(GraphAdapter):
    def __init__(
        self,
        target_id: str,
        timeout_seconds: float,
        *,
        host: str,
        port: int,
        password: str | None,
        graph_name: str,
    ) -> None:
        super().__init__(target_id, timeout_seconds)
        self._host = host
        self._port = port
        self._password = password
        self._graph_name = graph_name
        self._client: Any = None
        self._graph: Any = None

    def connect(self) -> None:
        self._client = FalkorDB(host=self._host, port=self._port, password=self._password)
        self._graph = self._client.select_graph(self._graph_name)
        self.trivial_query()

    def close(self) -> None:
        if self._client is not None:
            close = getattr(self._client, "close", None)
            if callable(close):
                close()
        self._client = None
        self._graph = None

    def reset(self) -> None:
        if self._graph is None:
            raise RuntimeError("Adapter is not connected")
        try:
            self._graph.delete()
        except Exception as error:
            message = str(error).lower()
            if "does not exist" not in message and "unknown graph" not in message:
                raise
        self._graph = self._client.select_graph(self._graph_name)

    def create_schema(self) -> None:
        for statement in (
            "CREATE INDEX FOR (user:User) ON (user.userId)",
            "CREATE INDEX FOR (movie:Movie) ON (movie.movieId)",
            "CREATE INDEX FOR (movie:Movie) ON (movie.year)",
        ):
            self._query(statement)

    def load_users(self, rows: Sequence[dict[str, Any]]) -> None:
        self._query(
            "UNWIND $rows AS row CREATE (:User {userId: row.userId})",
            {"rows": list(rows)},
        )

    def load_movies(self, rows: Sequence[dict[str, Any]]) -> None:
        self._query(
            """
            UNWIND $rows AS row
            CREATE (:Movie {movieId: row.movieId, title: row.title,
                            year: row.year, genres: row.genres})
            """,
            {"rows": list(rows)},
        )

    def load_ratings(self, rows: Sequence[dict[str, Any]]) -> None:
        self._query(
            """
            UNWIND $rows AS row
            MATCH (user:User {userId: row.userId}), (movie:Movie {movieId: row.movieId})
            CREATE (user)-[:RATED {rating: row.rating, timestamp: row.timestamp}]->(movie)
            """,
            {"rows": list(rows)},
        )

    def counts(self) -> dict[str, int]:
        queries = {
            "users": "MATCH (user:User) RETURN count(user) AS value",
            "movies": "MATCH (movie:Movie) RETURN count(movie) AS value",
            "relationships": "MATCH ()-[rating:RATED]->() RETURN count(rating) AS value",
        }
        return {key: int(self._query(query)[0]["value"]) for key, query in queries.items()}

    def integrity(self) -> dict[str, int]:
        return {
            key: int(self._query(query)[0]["value"]) for key, query in INTEGRITY_QUERIES.items()
        }

    def explain(self, workload: str, parameter: int | None = None) -> dict[str, Any]:
        if self._graph is None:
            raise RuntimeError("Adapter is not connected")
        try:
            query = READ_QUERIES[workload]
        except KeyError as error:
            raise ValueError(f"Unknown workload: {workload}") from error
        parameters = {} if workload == "aggregation" else {"value": parameter}
        plan = self._graph.explain(query, params=parameters)
        return {"format": "falkordb_plan", "lines": list(plan.plan)}

    def read(self, workload: str, parameter: int | None = None) -> list[dict[str, Any]]:
        query = READ_QUERIES[workload]
        parameters = {} if workload == "aggregation" else {"value": parameter}
        return self._query(query, parameters)

    def write_token(self, user_id: int, token: str) -> list[dict[str, Any]]:
        return self._query(
            "MATCH (user:User {userId: $userId}) SET user.benchmarkToken = $token "
            "RETURN user.userId AS userId",
            {"userId": user_id, "token": token},
        )

    def trivial_query(self) -> list[dict[str, Any]]:
        return self._query("RETURN 1 AS value")

    def version(self) -> str:
        rows = self._query("CALL dbms.procedures() YIELD name RETURN count(name) AS procedures")
        if rows:
            return "FalkorDB (live version captured by container evidence)"
        return "not observable"

    def _query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._graph is None:
            raise RuntimeError("Adapter is not connected")
        result = self._graph.query(
            query,
            params=parameters or {},
            timeout=int(self.timeout_seconds * 1000),
        )
        header = [self._header_name(item) for item in getattr(result, "header", [])]
        return [
            {header[index]: self._decode(value) for index, value in enumerate(row)}
            for row in getattr(result, "result_set", [])
        ]

    @staticmethod
    def _header_name(value: Any) -> str:
        if isinstance(value, (list, tuple)):
            value = value[-1]
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    @staticmethod
    def _decode(value: Any) -> Any:
        return value.decode("utf-8") if isinstance(value, bytes) else value
