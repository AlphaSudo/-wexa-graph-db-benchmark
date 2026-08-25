from wexa_benchmark.adapters.cypher import _serialize_plan


def test_neo4j_driver_mapping_plan_is_json_serializable() -> None:
    plan = {
        "operatorType": "ProduceResults",
        "identifiers": ["movie"],
        "args": {"Details": "movie.movieId"},
        "children": [
            {
                "operatorType": "NodeUniqueIndexSeek",
                "identifiers": ["movie"],
                "args": {},
                "children": [],
            }
        ],
    }
    serialized = _serialize_plan(plan)
    assert serialized["operator_type"] == "ProduceResults"
    assert serialized["children"][0]["operator_type"] == "NodeUniqueIndexSeek"
