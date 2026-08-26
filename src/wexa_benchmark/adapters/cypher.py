from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from neo4j import GraphDatabase

from .base import GraphAdapter

READ_QUERIES = {
    "hop_1": """
        MATCH (:User {userId: $value})-[:RATED]->(movie:Movie)
        RETURN movie.movieId AS movieId ORDER BY movieId
    """,
    "hop_2": """
        MATCH (:User {userId: $value})-[:RATED]->(:Movie)<-[:RATED]-(peer:User)
        WHERE peer.userId <> $value
        RETURN DISTINCT peer.userId AS peerId ORDER BY peerId
    """,
    "hop_3": """
        MATCH (:User {userId: $value})-[:RATED]->(:Movie)<-[:RATED]-(peer:User)
        WHERE peer.userId <> $value
        WITH DISTINCT peer
        MATCH (peer)-[:RATED]->(movie:Movie)
        RETURN DISTINCT movie.movieId AS movieId ORDER BY movieId
    """,
    "point_lookup": """
        MATCH (movie:Movie {movieId: $value})
        RETURN movie.movieId AS movieId, movie.title AS title, movie.year AS year
    """,
    "filtered_lookup": """
        MATCH (movie:Movie {year: $value})
        RETURN movie.movieId AS movieId ORDER BY movieId
    """,
    "aggregation": """
        MATCH ()-[rating:RATED]->()
        RETURN rating.rating AS rating, count(*) AS count ORDER BY rating
    """,
}

INTEGRITY_QUERIES = {
    "unique_user_ids": "MATCH (user:User) RETURN count(DISTINCT user.userId) AS value",
    "unique_movie_ids": "MATCH (movie:Movie) RETURN count(DISTINCT movie.movieId) AS value",
    "duplicate_rating_edge_keys": """
        MATCH (user:User)-[rating:RATED]->(movie:Movie)
        WITH user.userId AS userId, movie.movieId AS movieId, count(rating) AS occurrences
        WHERE occurrences > 1
        RETURN coalesce(sum(occurrences - 1), 0) AS value
    """,
    "invalid_relationship_endpoints": """
        MATCH (source)-[rating:RATED]->(target)
        WHERE NOT source:User OR NOT target:Movie
           OR source.userId IS NULL OR target.movieId IS NULL
        RETURN count(rating) AS value
    """,
    "rating_tenths_sum": """
        MATCH ()-[rating:RATED]->()
        RETURN sum(toInteger(rating.rating * 10)) AS value
    """,
    "timestamp_min": "MATCH ()-[rating:RATED]->() RETURN min(rating.timestamp) AS value",
    "timestamp_max": "MATCH ()-[rating:RATED]->() RETURN max(rating.timestamp) AS value",
    "timestamp_sum": "MATCH ()-[rating:RATED]->() RETURN sum(rating.timestamp) AS value",
    "movie_year_null_count": """
        MATCH (movie:Movie) WHERE movie.year IS NULL RETURN count(movie) AS value
    """,
}


class CypherAdapter(GraphAdapter):
    def __init__(
        self,
        target_id: str,
        timeout_seconds: float,
        *,
        uri: str,
        username: str | None,
        password: str | None,
        database: str | None,
        dialect: str,
    ) -> None:
        super().__init__(target_id, timeout_seconds)
        self._uri = uri
        if (username is None) != (password is None):
            raise ValueError("Cypher credentials require both username and password")
        self._auth: tuple[str, str] | None = (
            (username, password) if username is not None and password is not None else None
        )
        self._database = database
        self._dialect = dialect
        self._driver: Any = None

    def connect(self) -> None:
        self._driver = GraphDatabase.driver(
            self._uri,
            auth=self._auth,
            connection_timeout=self.timeout_seconds,
            max_connection_pool_size=50,
            connection_acquisition_timeout=self.timeout_seconds,
        )
        self._driver.verify_connectivity()

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def reset(self) -> None:
        while True:
            rows = self._run(
                "MATCH ()-[relationship]->() WITH relationship LIMIT 2000 "
                "DELETE relationship RETURN count(*) AS deleted"
            )
            if not rows or int(rows[0]["deleted"]) == 0:
                break
        while True:
            rows = self._run(
                "MATCH (node) WITH node LIMIT 1000 DELETE node RETURN count(*) AS deleted"
            )
            if not rows or int(rows[0]["deleted"]) == 0:
                break

    def create_schema(self) -> None:
        if self._dialect == "memgraph":
            statements = [
                "CREATE CONSTRAINT ON (user:User) ASSERT user.userId IS UNIQUE",
                "CREATE CONSTRAINT ON (movie:Movie) ASSERT movie.movieId IS UNIQUE",
                "CREATE INDEX ON :Movie(year)",
            ]
        else:
            statements = [
                "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
                "FOR (user:User) REQUIRE user.userId IS UNIQUE",
                "CREATE CONSTRAINT movie_id_unique IF NOT EXISTS "
                "FOR (movie:Movie) REQUIRE movie.movieId IS UNIQUE",
                "CREATE INDEX movie_year IF NOT EXISTS FOR (movie:Movie) ON (movie.year)",
            ]
        for statement in statements:
            try:
                self._run(statement)
            except Exception as error:
                message = str(error).lower()
                if "already exists" not in message and "equivalent" not in message:
                    raise
        if self._dialect != "memgraph" and self.target_id != "cognodb-c0":
            self._run("CALL db.awaitIndexes($timeout)", {"timeout": int(self.timeout_seconds * 2)})

    def load_users(self, rows: Sequence[dict[str, Any]]) -> None:
        self._run(
            "UNWIND $rows AS row CREATE (:User {userId: row.userId})",
            {"rows": list(rows)},
        )

    def load_movies(self, rows: Sequence[dict[str, Any]]) -> None:
        self._run(
            """
            UNWIND $rows AS row
            CREATE (:Movie {movieId: row.movieId, title: row.title,
                            year: row.year, genres: row.genres})
            """,
            {"rows": list(rows)},
        )

    def load_ratings(self, rows: Sequence[dict[str, Any]]) -> None:
        self._run(
            """
            UNWIND $rows AS row
            MATCH (user:User {userId: row.userId})
            MATCH (movie:Movie {movieId: row.movieId})
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
        return {key: int(self._run(query)[0]["value"]) for key, query in queries.items()}

    def integrity(self) -> dict[str, int]:
        return {key: int(self._run(query)[0]["value"]) for key, query in INTEGRITY_QUERIES.items()}

    def explain(self, workload: str, parameter: int | None = None) -> dict[str, Any]:
        try:
            query = READ_QUERIES[workload]
        except KeyError as error:
            raise ValueError(f"Unknown workload: {workload}") from error
        parameters = {} if workload == "aggregation" else {"value": parameter}
        if self._dialect == "memgraph":
            return {"format": "records", "rows": self._run(f"EXPLAIN {query}", parameters)}
        if self._driver is None:
            raise RuntimeError("Adapter is not connected")
        session_kwargs = {"database": self._database} if self._database else {}
        with self._driver.session(**session_kwargs) as session:
            result = session.run(f"EXPLAIN {query}", parameters, timeout=self.timeout_seconds)
            plan = result.consume().plan
        if plan is None:
            return {"format": "not_observable"}
        return {"format": "neo4j_plan", "root": _serialize_plan(plan)}

    def read(self, workload: str, parameter: int | None = None) -> list[dict[str, Any]]:
        try:
            query = READ_QUERIES[workload]
        except KeyError as error:
            raise ValueError(f"Unknown workload: {workload}") from error
        parameters = {} if workload == "aggregation" else {"value": parameter}
        return self._run(query, parameters)

    def write_token(self, user_id: int, token: str) -> list[dict[str, Any]]:
        return self._run(
            """
            MATCH (user:User {userId: $userId})
            SET user.benchmarkToken = $token
            RETURN user.userId AS userId
            """,
            {"userId": user_id, "token": token},
        )

    def trivial_query(self) -> list[dict[str, Any]]:
        return self._run("RETURN 1 AS value")

    def version(self) -> str:
        if self.target_id == "cognodb-c0":
            return "CognoDB Cloud (version not observable via Cypher)"
        if self._dialect == "memgraph":
            rows = self._run("SHOW VERSION")
            return str(rows[0].get("version", rows[0])) if rows else "not observable"
        rows = self._run(
            "CALL dbms.components() YIELD name, versions "
            "WHERE name CONTAINS 'Neo4j' "
            "RETURN versions[0] AS version ORDER BY name LIMIT 1"
        )
        return str(rows[0]["version"]) if rows else "not observable"

    def _run(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._driver is None:
            raise RuntimeError("Adapter is not connected")
        session_kwargs = {"database": self._database} if self._database else {}
        with self._driver.session(**session_kwargs) as session:
            result = session.run(query, parameters or {}, timeout=self.timeout_seconds)
            return [record.data() for record in result]


def _serialize_plan(plan: Any) -> dict[str, Any]:
    if isinstance(plan, dict):
        arguments = plan.get("args", plan.get("arguments", {}))
        return {
            "operator_type": str(plan.get("operatorType", plan.get("operator_type", "unknown"))),
            "identifiers": sorted(str(value) for value in plan.get("identifiers", [])),
            "arguments": {str(key): str(value) for key, value in arguments.items()},
            "children": [_serialize_plan(child) for child in plan.get("children", [])],
        }
    return {
        "operator_type": str(plan.operator_type),
        "identifiers": sorted(str(identifier) for identifier in plan.identifiers),
        "arguments": {str(key): str(value) for key, value in plan.arguments.items()},
        "children": [_serialize_plan(child) for child in plan.children],
    }
