import json
from pathlib import Path

import pytest

from wexa_benchmark.dataset import (
    _build_query_bank,
    _distribution,
    _validate_source_integrity,
)
from wexa_benchmark.util import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def test_committed_official_manifest_and_query_bank_match() -> None:
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    query_bank_path = ROOT / "data" / "query_bank.json"
    query_bank = json.loads(query_bank_path.read_text(encoding="utf-8"))
    assert manifest["counts"] == {
        "users": 610,
        "movies": 9742,
        "nodes": 10352,
        "relationships": 100836,
    }
    assert manifest["integrity"]["duplicate_rating_edge_keys"] == 0
    assert manifest["sha256"]["query_bank"] == sha256_file(query_bank_path)
    assert query_bank["starts_per_bucket"] == 25
    assert len(query_bank["traversal_starts"]) == 100


def test_source_integrity_rejects_duplicate_rating_keys() -> None:
    movies = [{"movieId": 10}]
    ratings = [
        {"userId": 1, "movieId": 10, "rating": 4.0, "timestamp": 1},
        {"userId": 1, "movieId": 10, "rating": 4.5, "timestamp": 2},
    ]
    with pytest.raises(ValueError, match=r"duplicate .* rating keys"):
        _validate_source_integrity([1], movies, ratings)


def test_degree_distribution_uses_nearest_rank_percentiles() -> None:
    assert _distribution([1, 2, 3, 4]) == {
        "min": 1,
        "p25": 1,
        "p50": 2,
        "p75": 3,
        "p95": 4,
        "max": 4,
        "mean": 2.5,
    }


def test_query_bank_records_all_rank_bucket_boundaries() -> None:
    users = list(range(1, 9))
    movies = [
        {"movieId": movie_id, "title": f"Movie {movie_id}", "year": 2000, "genres": []}
        for movie_id in range(1, 9)
    ]
    ratings = [
        {"userId": user_id, "movieId": user_id, "rating": 4.0, "timestamp": user_id}
        for user_id in users
    ]
    bank = _build_query_bank(users, movies, ratings, seed=7, starts_per_bucket=1)
    assert bank["schema_version"] == 2
    assert set(bank["degree_buckets"]) == {"low", "medium", "high", "hub"}
    assert sum(bucket["candidate_count"] for bucket in bank["degree_buckets"].values()) == len(
        users
    )
    assert len(bank["traversal_starts"]) == 4
