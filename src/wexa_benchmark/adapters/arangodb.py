from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from urllib.parse import quote

import httpx

from .base import GraphAdapter


class ArangoAdapter(GraphAdapter):
    def __init__(
        self,
        target_id: str,
        timeout_seconds: float,
        *,
        url: str,
        username: str | None,
        password: str | None,
        database: str,
    ) -> None:
        super().__init__(target_id, timeout_seconds)
        self._url = url.rstrip("/")
        if (username is None) != (password is None):
            raise ValueError("ArangoDB credentials require both username and password")
        self._auth: tuple[str, str] | None = (
            (username, password) if username is not None and password is not None else None
        )
        self._database = database
        self._client: httpx.Client | None = None

    def connect(self) -> None:
        system = self._system_client()
        response = system.get("/_api/version")
        response.raise_for_status()
        databases = system.get("/_api/database/user").json()["result"]
        if self._database not in databases:
            response = system.post("/_api/database", json={"name": self._database})
            response.raise_for_status()
        system.close()
        self._client = self._database_client()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def reset(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        system = self._system_client()
        databases = system.get("/_api/database/user").json()["result"]
        if self._database in databases:
            response = system.delete(f"/_api/database/{quote(self._database, safe='')}")
            response.raise_for_status()
        response = system.post("/_api/database", json={"name": self._database})
        response.raise_for_status()
        system.close()
        self._client = self._database_client()

    def create_schema(self) -> None:
        for name, collection_type in (("users", 2), ("movies", 2), ("rated", 3)):
            self._request("POST", "/_api/collection", json={"name": name, "type": collection_type})
        indexes = (
            ("users", {"type": "persistent", "fields": ["userId"], "unique": True}),
            ("movies", {"type": "persistent", "fields": ["movieId"], "unique": True}),
            ("movies", {"type": "persistent", "fields": ["year"], "unique": False}),
        )
        for collection, definition in indexes:
            self._request("POST", f"/_api/index?collection={collection}", json=definition)

    def load_users(self, rows: Sequence[dict[str, Any]]) -> None:
        documents = [{"_key": str(row["userId"]), "userId": row["userId"]} for row in rows]
        self._documents("users", documents)

    def load_movies(self, rows: Sequence[dict[str, Any]]) -> None:
        documents = [{"_key": str(row["movieId"]), **row} for row in rows]
        self._documents("movies", documents)

    def load_ratings(self, rows: Sequence[dict[str, Any]]) -> None:
        documents = [
            {
                "_key": f"{row['userId']}-{row['movieId']}",
                "_from": f"users/{row['userId']}",
                "_to": f"movies/{row['movieId']}",
                "rating": row["rating"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
        self._documents("rated", documents)

    def counts(self) -> dict[str, int]:
        rows = self._aql(
            "RETURN {users: LENGTH(users), movies: LENGTH(movies), relationships: LENGTH(rated)}"
        )
        return {key: int(rows[0][key]) for key in ("users", "movies", "relationships")}

    def integrity(self) -> dict[str, int]:
        duplicate_rows = self._aql(
            "FOR edge IN rated "
            "COLLECT source = edge._from, target = edge._to WITH COUNT INTO occurrences "
            "FILTER occurrences > 1 COLLECT AGGREGATE value = SUM(occurrences - 1) "
            "RETURN {value}"
        )
        aggregates = self._aql(
            "FOR edge IN rated COLLECT AGGREGATE "
            "rating_tenths_sum = SUM(ROUND(edge.rating * 10)), "
            "timestamp_min = MIN(edge.timestamp), timestamp_max = MAX(edge.timestamp), "
            "timestamp_sum = SUM(edge.timestamp) "
            "RETURN {rating_tenths_sum, timestamp_min, timestamp_max, timestamp_sum}"
        )[0]
        values = {
            "unique_user_ids": self._scalar_aql(
                "RETURN LENGTH(UNIQUE(FOR user IN users RETURN user.userId))"
            ),
            "unique_movie_ids": self._scalar_aql(
                "RETURN LENGTH(UNIQUE(FOR movie IN movies RETURN movie.movieId))"
            ),
            "duplicate_rating_edge_keys": int(duplicate_rows[0].get("value") or 0)
            if duplicate_rows
            else 0,
            "invalid_relationship_endpoints": self._scalar_aql(
                "RETURN LENGTH(FOR edge IN rated "
                "FILTER DOCUMENT(edge._from) == null OR DOCUMENT(edge._to) == null "
                "OR !IS_SAME_COLLECTION('users', edge._from) "
                "OR !IS_SAME_COLLECTION('movies', edge._to) RETURN 1)"
            ),
            "movie_year_null_count": self._scalar_aql(
                "RETURN LENGTH(FOR movie IN movies FILTER movie.year == null RETURN 1)"
            ),
        }
        values.update({key: int(value) for key, value in aggregates.items()})
        return values

    def explain(self, workload: str, parameter: int | None = None) -> dict[str, Any]:
        query, bind_vars = self._read_query(workload, parameter)
        payload = self._request(
            "POST",
            "/_api/explain",
            json={"query": query, "bindVars": bind_vars, "options": {"allPlans": False}},
        ).json()
        plan = payload.get("plan", {})
        return {
            "format": "aql_plan",
            "estimated_cost": plan.get("estimatedCost"),
            "estimated_items": plan.get("estimatedNrItems"),
            "collections": plan.get("collections", []),
            "rules": plan.get("rules", []),
            "nodes": [
                {
                    "id": node.get("id"),
                    "type": node.get("type"),
                    "dependencies": node.get("dependencies", []),
                    "estimated_cost": node.get("estimatedCost"),
                    "estimated_items": node.get("estimatedNrItems"),
                }
                for node in plan.get("nodes", [])
            ],
        }

    def read(self, workload: str, parameter: int | None = None) -> list[dict[str, Any]]:
        query, bind_vars = self._read_query(workload, parameter)
        rows = self._aql(query, bind_vars)
        if workload == "aggregation":
            for row in rows:
                row["rating"] = float(row["rating"])
        return rows

    def write_token(self, user_id: int, token: str) -> list[dict[str, Any]]:
        return self._aql(
            "UPDATE @key WITH {benchmarkToken: @token} IN users RETURN {userId: NEW.userId}",
            {"key": str(user_id), "token": token},
        )

    def trivial_query(self) -> list[dict[str, Any]]:
        return self._aql("RETURN {value: 1}")

    def version(self) -> str:
        response = self._request("GET", "/_api/version")
        return str(response.json().get("version", "not observable"))

    def _read_query(self, workload: str, parameter: int | None) -> tuple[str, dict[str, Any]]:
        user_key = f"users/{parameter}" if parameter is not None else None
        queries = {
            "hop_1": (
                "FOR edge IN rated FILTER edge._from == @user "
                "LET movieId = TO_NUMBER(PARSE_IDENTIFIER(edge._to).key) "
                "SORT movieId RETURN {movieId}",
                {"user": user_key},
            ),
            "hop_2": (
                "LET movieKeys = (FOR edge IN rated FILTER edge._from == @user RETURN edge._to) "
                "FOR edge IN rated FILTER edge._to IN movieKeys AND edge._from != @user "
                "COLLECT peerId = TO_NUMBER(PARSE_IDENTIFIER(edge._from).key) "
                "SORT peerId RETURN {peerId}",
                {"user": user_key},
            ),
            "hop_3": (
                "LET movieKeys = (FOR edge IN rated FILTER edge._from == @user RETURN edge._to) "
                "LET peers = UNIQUE(FOR edge IN rated FILTER edge._to IN movieKeys "
                "AND edge._from != @user RETURN edge._from) "
                "FOR edge IN rated FILTER edge._from IN peers "
                "COLLECT movieId = TO_NUMBER(PARSE_IDENTIFIER(edge._to).key) "
                "SORT movieId RETURN {movieId}",
                {"user": user_key},
            ),
            "point_lookup": (
                "LET movie = DOCUMENT('movies', @key) "
                "FILTER movie != null "
                "RETURN {movieId: movie.movieId, title: movie.title, year: movie.year}",
                {"key": str(parameter)},
            ),
            "filtered_lookup": (
                "FOR movie IN movies FILTER movie.year == @year SORT movie.movieId "
                "RETURN {movieId: movie.movieId}",
                {"year": parameter},
            ),
            "aggregation": (
                "FOR edge IN rated COLLECT rating = edge.rating WITH COUNT INTO count "
                "SORT rating RETURN {rating, count}",
                {},
            ),
        }
        try:
            return queries[workload]
        except KeyError as error:
            raise ValueError(f"Unknown workload: {workload}") from error

    def _aql(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        response = self._request(
            "POST",
            "/_api/cursor",
            json={"query": query, "bindVars": bind_vars or {}, "batchSize": 5000},
        )
        payload = response.json()
        rows = list(payload.get("result", []))
        cursor_id = payload.get("id")
        while payload.get("hasMore") and cursor_id:
            payload = self._request("PUT", f"/_api/cursor/{cursor_id}").json()
            rows.extend(payload.get("result", []))
        return rows

    def _scalar_aql(self, query: str) -> int:
        response = self._request(
            "POST",
            "/_api/cursor",
            json={"query": query, "bindVars": {}, "batchSize": 1},
        )
        rows = response.json().get("result", [])
        if len(rows) != 1:
            raise ValueError(f"Expected one scalar AQL result, found {len(rows)}")
        return int(rows[0])

    def _documents(self, collection: str, documents: list[dict[str, Any]]) -> None:
        self._request(
            "POST",
            f"/_api/document/{collection}?waitForSync=false&silent=true",
            json=documents,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if self._client is None:
            raise RuntimeError("Adapter is not connected")
        response = self._client.request(method, path, **kwargs)
        response.raise_for_status()
        return response

    def _system_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=f"{self._url}/_db/_system",
            auth=self._auth,
            timeout=self.timeout_seconds,
        )

    def _database_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=f"{self._url}/_db/{quote(self._database, safe='')}",
            auth=self._auth,
            timeout=self.timeout_seconds,
        )
