from __future__ import annotations

import csv
import json
import math
import random
import re
import urllib.request
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import DatasetConfig
from .util import canonical_json, normalized_rows, sha256_file, stable_digest

YEAR_PATTERN = re.compile(r"\((\d{4})\)$")


@dataclass(frozen=True)
class PreparedDataset:
    root: Path
    users_path: Path
    movies_path: Path
    ratings_path: Path
    manifest_path: Path
    query_bank_path: Path
    manifest: dict[str, Any]
    query_bank: dict[str, Any]


def prepare_dataset(config: DatasetConfig, seed: int, repository_root: Path) -> PreparedDataset:
    data_root = repository_root / "data"
    raw_root = data_root / "raw"
    normalized_root = data_root / "normalized"
    raw_root.mkdir(parents=True, exist_ok=True)
    normalized_root.mkdir(parents=True, exist_ok=True)

    archive_path = raw_root / f"{config.name}.zip"
    if not archive_path.exists():
        _download(config.url, archive_path)

    movies, ratings, source_readme = _read_archive(archive_path)
    user_ids = sorted({row["userId"] for row in ratings})
    if len(user_ids) != config.expected_users:
        raise ValueError(f"Expected {config.expected_users} users, found {len(user_ids)}")
    if len(movies) != config.expected_movies:
        raise ValueError(f"Expected {config.expected_movies} movies, found {len(movies)}")
    if len(ratings) != config.expected_relationships:
        raise ValueError(
            f"Expected {config.expected_relationships} relationships, found {len(ratings)}"
        )
    _validate_source_integrity(user_ids, movies, ratings)

    users_path = normalized_root / "users.csv"
    movies_path = normalized_root / "movies.csv"
    ratings_path = normalized_root / "ratings.csv"
    source_readme_path = data_root / "MOVIELENS_README.txt"
    _write_csv(users_path, ["userId"], ({"userId": user_id} for user_id in user_ids))
    _write_csv(
        movies_path,
        ["movieId", "title", "year", "genres"],
        (
            {
                "movieId": row["movieId"],
                "title": row["title"],
                "year": "" if row["year"] is None else row["year"],
                "genres": "|".join(row["genres"]),
            }
            for row in movies
        ),
    )
    _write_csv(
        ratings_path,
        ["userId", "movieId", "rating", "timestamp"],
        ratings,
    )
    source_readme_path.write_bytes(source_readme)

    query_bank = _build_query_bank(
        user_ids,
        movies,
        ratings,
        seed=seed,
        starts_per_bucket=config.query_starts_per_bucket,
    )
    query_bank_path = data_root / "query_bank.json"
    query_bank_path.write_text(canonical_json(query_bank) + "\n", encoding="utf-8")

    archive_sha256 = sha256_file(archive_path)
    manifest = {
        "schema_version": 2,
        "dataset": config.name,
        "source": {
            "url": config.url,
            "retrieved_at_utc": _retrieval_timestamp(data_root, archive_path, archive_sha256),
            "retrieval_time_basis": "local archive creation time on first preparation",
            "archive_size_bytes": archive_path.stat().st_size,
            "archive_member_readme": _member_name(archive_path, "README.txt"),
            "license": "MovieLens dataset usage license; see MOVIELENS_README.txt",
        },
        "counts": {
            "users": len(user_ids),
            "movies": len(movies),
            "nodes": len(user_ids) + len(movies),
            "relationships": len(ratings),
        },
        "integrity": _integrity_statistics(user_ids, movies, ratings),
        "property_contract": _property_contract(movies),
        "sha256": {
            "archive": archive_sha256,
            "users": sha256_file(users_path),
            "movies": sha256_file(movies_path),
            "ratings": sha256_file(ratings_path),
            "query_bank": sha256_file(query_bank_path),
            "source_readme": sha256_file(source_readme_path),
        },
    }
    manifest_path = data_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return PreparedDataset(
        root=data_root,
        users_path=users_path,
        movies_path=movies_path,
        ratings_path=ratings_path,
        manifest_path=manifest_path,
        query_bank_path=query_bank_path,
        manifest=manifest,
        query_bank=query_bank,
    )


def load_prepared_dataset(repository_root: Path) -> PreparedDataset:
    data_root = repository_root / "data"
    manifest_path = data_root / "manifest.json"
    query_bank_path = data_root / "query_bank.json"
    source_readme_path = data_root / "MOVIELENS_README.txt"
    normalized_root = data_root / "normalized"
    paths = {
        "users": normalized_root / "users.csv",
        "movies": normalized_root / "movies.csv",
        "ratings": normalized_root / "ratings.csv",
    }
    required = [manifest_path, query_bank_path, *paths.values()]
    required.append(source_readme_path)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Dataset is not prepared; missing: {', '.join(missing)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, path in {
        **paths,
        "query_bank": query_bank_path,
        "source_readme": source_readme_path,
    }.items():
        expected = manifest["sha256"][name]
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"Checksum mismatch for {name}: expected {expected}, found {actual}")
    return PreparedDataset(
        root=data_root,
        users_path=paths["users"],
        movies_path=paths["movies"],
        ratings_path=paths["ratings"],
        manifest_path=manifest_path,
        query_bank_path=query_bank_path,
        manifest=manifest,
        query_bank=json.loads(query_bank_path.read_text(encoding="utf-8")),
    )


def read_users(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return [{"userId": int(row["userId"])} for row in csv.DictReader(stream)]


def read_movies(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return [
            {
                "movieId": int(row["movieId"]),
                "title": row["title"],
                "year": int(row["year"]) if row["year"] else None,
                "genres": row["genres"].split("|") if row["genres"] else [],
            }
            for row in csv.DictReader(stream)
        ]


def read_ratings(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return [
            {
                "userId": int(row["userId"]),
                "movieId": int(row["movieId"]),
                "rating": float(row["rating"]),
                "timestamp": int(row["timestamp"]),
            }
            for row in csv.DictReader(stream)
        ]


def _download(url: str, destination: Path) -> None:
    temporary = destination.with_suffix(".part")
    request = urllib.request.Request(url, headers={"User-Agent": "wexa-benchmark/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    temporary.replace(destination)


def _read_archive(
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bytes]:
    with zipfile.ZipFile(path) as archive:
        movie_name = _single_member(archive, "movies.csv")
        rating_name = _single_member(archive, "ratings.csv")
        readme_name = _single_member(archive, "README.txt")
        with archive.open(movie_name) as movie_bytes:
            movie_lines = (line.decode("utf-8") for line in movie_bytes)
            movies = []
            for row in csv.DictReader(movie_lines):
                match = YEAR_PATTERN.search(row["title"])
                movies.append(
                    {
                        "movieId": int(row["movieId"]),
                        "title": row["title"],
                        "year": int(match.group(1)) if match else None,
                        "genres": []
                        if row["genres"] == "(no genres listed)"
                        else row["genres"].split("|"),
                    }
                )
        with archive.open(rating_name) as rating_bytes:
            rating_lines = (line.decode("utf-8") for line in rating_bytes)
            ratings = [
                {
                    "userId": int(row["userId"]),
                    "movieId": int(row["movieId"]),
                    "rating": float(row["rating"]),
                    "timestamp": int(row["timestamp"]),
                }
                for row in csv.DictReader(rating_lines)
            ]
        source_readme = archive.read(readme_name)
    return movies, ratings, source_readme


def _member_name(path: Path, filename: str) -> str:
    with zipfile.ZipFile(path) as archive:
        return _single_member(archive, filename)


def _retrieval_timestamp(data_root: Path, archive_path: Path, archive_sha256: str) -> str:
    manifest_path = data_root / "manifest.json"
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            if previous.get("sha256", {}).get("archive") == archive_sha256:
                timestamp = previous.get("source", {}).get("retrieved_at_utc")
                if timestamp:
                    return str(timestamp)
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    created = datetime.fromtimestamp(archive_path.stat().st_ctime, UTC)
    return created.isoformat().replace("+00:00", "Z")


def _single_member(archive: zipfile.ZipFile, filename: str) -> str:
    matches = [name for name in archive.namelist() if Path(name).name == filename]
    if len(matches) != 1:
        raise ValueError(f"Expected one {filename} in archive, found {len(matches)}")
    return matches[0]


def _write_csv(path: Path, fields: list[str], rows: Any) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _validate_source_integrity(
    user_ids: list[int],
    movies: list[dict[str, Any]],
    ratings: list[dict[str, Any]],
) -> None:
    movie_ids = [int(movie["movieId"]) for movie in movies]
    if len(set(movie_ids)) != len(movie_ids):
        raise ValueError("Source contains duplicate movieId values")
    edge_keys = [(int(row["userId"]), int(row["movieId"])) for row in ratings]
    if len(set(edge_keys)) != len(edge_keys):
        raise ValueError("Source contains duplicate (userId, movieId) rating keys")
    user_id_set = set(user_ids)
    movie_id_set = set(movie_ids)
    if any(
        user_id not in user_id_set or movie_id not in movie_id_set
        for user_id, movie_id in edge_keys
    ):
        raise ValueError("Source contains a rating with a missing endpoint")
    if any(
        not math.isfinite(float(row["rating"]))
        or float(row["rating"]) * 2 != round(float(row["rating"]) * 2)
        for row in ratings
    ):
        raise ValueError("Source contains a non-finite or non-half-step rating")


def _build_query_bank(
    user_ids: list[int],
    movies: list[dict[str, Any]],
    ratings: list[dict[str, Any]],
    *,
    seed: int,
    starts_per_bucket: int,
) -> dict[str, Any]:
    randomizer = random.Random(seed)
    user_to_movies: dict[int, set[int]] = defaultdict(set)
    movie_to_users: dict[int, set[int]] = defaultdict(set)
    rating_counts: Counter[float] = Counter()
    for rating in ratings:
        user_id = rating["userId"]
        movie_id = rating["movieId"]
        user_to_movies[user_id].add(movie_id)
        movie_to_users[movie_id].add(user_id)
        rating_counts[rating["rating"]] += 1

    ranked = sorted(user_ids, key=lambda user_id: (len(user_to_movies[user_id]), user_id))
    count = len(ranked)
    buckets = {
        "low": ranked[: count // 4],
        "medium": ranked[count // 4 : (3 * count) // 4],
        "high": ranked[(3 * count) // 4 : (95 * count) // 100],
        "hub": ranked[(95 * count) // 100 :],
    }
    bucket_metadata = {
        bucket_name: {
            "rank_start_inclusive": min(ranked.index(user_id) for user_id in candidates),
            "rank_end_exclusive": max(ranked.index(user_id) for user_id in candidates) + 1,
            "candidate_count": len(candidates),
            "min_degree": min(len(user_to_movies[user_id]) for user_id in candidates),
            "max_degree": max(len(user_to_movies[user_id]) for user_id in candidates),
        }
        for bucket_name, candidates in buckets.items()
    }
    starts: list[dict[str, Any]] = []
    for bucket_name, candidates in buckets.items():
        if len(candidates) < starts_per_bucket:
            raise ValueError(f"Bucket {bucket_name} has fewer than {starts_per_bucket} users")
        for user_id in sorted(randomizer.sample(candidates, starts_per_bucket)):
            hop_1 = sorted(user_to_movies[user_id])
            hop_2 = sorted(
                {peer for movie_id in hop_1 for peer in movie_to_users[movie_id] if peer != user_id}
            )
            hop_3 = sorted({movie for peer in hop_2 for movie in user_to_movies[peer]})
            starts.append(
                {
                    "userId": user_id,
                    "bucket": bucket_name,
                    "degree": len(hop_1),
                    "expected": {
                        "hop_1": _expected([{"movieId": value} for value in hop_1]),
                        "hop_2": _expected([{"peerId": value} for value in hop_2]),
                        "hop_3": _expected([{"movieId": value} for value in hop_3]),
                    },
                }
            )

    movie_by_id = {row["movieId"]: row for row in movies}
    movie_ids = sorted(movie_by_id)
    sampled_movies = sorted(randomizer.sample(movie_ids, min(100, len(movie_ids))))
    point_lookups = []
    for movie_id in sampled_movies:
        movie = movie_by_id[movie_id]
        row = {"movieId": movie_id, "title": movie["title"], "year": movie["year"]}
        point_lookups.append({"movieId": movie_id, "expected": _expected([row])})

    movies_by_year: dict[int, list[int]] = defaultdict(list)
    for movie in movies:
        if movie["year"] is not None:
            movies_by_year[movie["year"]].append(movie["movieId"])
    years = sorted(movies_by_year, key=lambda year: (-len(movies_by_year[year]), year))[:20]
    filtered_lookups = [
        {
            "year": year,
            "expected": _expected([{"movieId": value} for value in sorted(movies_by_year[year])]),
        }
        for year in years
    ]
    aggregation_rows = [
        {"rating": rating, "count": rating_counts[rating]} for rating in sorted(rating_counts)
    ]
    return {
        "schema_version": 2,
        "seed": seed,
        "starts_per_bucket": starts_per_bucket,
        "degree_buckets": bucket_metadata,
        "traversal_starts": starts,
        "point_lookups": point_lookups,
        "filtered_lookups": filtered_lookups,
        "aggregation": {"expected": _expected(aggregation_rows)},
    }


def _expected(rows: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = normalized_rows(rows)
    return {"count": len(normalized), "sha256": stable_digest(normalized)}


def _integrity_statistics(
    user_ids: list[int],
    movies: list[dict[str, Any]],
    ratings: list[dict[str, Any]],
) -> dict[str, Any]:
    movie_ids = [int(movie["movieId"]) for movie in movies]
    movie_id_set = set(movie_ids)
    user_id_set = set(user_ids)
    edge_keys = [(int(row["userId"]), int(row["movieId"])) for row in ratings]
    unique_edge_keys = set(edge_keys)
    invalid_endpoints = sum(
        1
        for user_id, movie_id in edge_keys
        if user_id not in user_id_set or movie_id not in movie_id_set
    )
    rating_tenths = [round(float(row["rating"]) * 10) for row in ratings]
    rating_counts = Counter(rating_tenths)
    timestamps = [int(row["timestamp"]) for row in ratings]
    years = [movie["year"] for movie in movies if movie["year"] is not None]
    year_counts = Counter(int(year) for year in years)
    user_degree = Counter(int(row["userId"]) for row in ratings)
    movie_degree = Counter(int(row["movieId"]) for row in ratings)
    return {
        "unique_user_ids": len(user_id_set),
        "unique_movie_ids": len(movie_id_set),
        "unique_rating_edge_keys": len(unique_edge_keys),
        "duplicate_rating_edge_keys": len(edge_keys) - len(unique_edge_keys),
        "invalid_relationship_endpoints": invalid_endpoints,
        "rating": {
            "tenths_sum": sum(rating_tenths),
            "counts_by_value": {
                f"{tenths / 10:.1f}": rating_counts[tenths] for tenths in sorted(rating_counts)
            },
        },
        "timestamp": {
            "min": min(timestamps),
            "max": max(timestamps),
            "sum": sum(timestamps),
        },
        "movie_year": {
            "null_count": len(movies) - len(years),
            "min": min(years),
            "max": max(years),
            "counts_by_year": {str(year): year_counts[year] for year in sorted(year_counts)},
        },
        "degree": {
            "users": _distribution([user_degree[user_id] for user_id in user_ids]),
            "movies": _distribution([movie_degree[movie_id] for movie_id in movie_ids]),
        },
    }


def _distribution(values: list[int]) -> dict[str, int | float]:
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "p25": _nearest_rank(ordered, 0.25),
        "p50": _nearest_rank(ordered, 0.50),
        "p75": _nearest_rank(ordered, 0.75),
        "p95": _nearest_rank(ordered, 0.95),
        "max": ordered[-1],
        "mean": sum(ordered) / len(ordered),
    }


def _nearest_rank(ordered: list[int], probability: float) -> int:
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * probability) - 1))
    return ordered[index]


def _property_contract(movies: list[dict[str, Any]]) -> dict[str, Any]:
    year_nulls = sum(movie["year"] is None for movie in movies)
    return {
        "User": {"userId": {"type": "integer", "null_count": 0}},
        "Movie": {
            "movieId": {"type": "integer", "null_count": 0},
            "title": {"type": "string", "null_count": 0},
            "year": {"type": "integer_or_null", "null_count": year_nulls},
            "genres": {"type": "list_of_strings", "null_count": 0},
        },
        "RATED": {
            "rating": {"type": "float", "null_count": 0},
            "timestamp": {"type": "integer", "null_count": 0},
        },
    }
