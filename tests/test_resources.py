from wexa_benchmark.resources import parse_size, parse_stats_line


def test_parse_size_supports_podman_decimal_and_binary_units() -> None:
    assert parse_size("13.23MB") == 13_230_000
    assert parse_size("512MiB") == 536_870_912
    assert parse_size("0B") == 0


def test_parse_stats_line_normalizes_all_units() -> None:
    sample = parse_stats_line(
        "abc|wexa-db|49.5|48.0|13.23MB / 536.9MB|2.46%|1.5kB / 698B|1.561MB / 0B|12"
    )
    assert sample["cpu_percent"] == 49.5
    assert sample["memory_usage_bytes"] == 13_230_000
    assert sample["memory_limit_bytes"] == 536_900_000
    assert sample["network_output_bytes"] == 698
    assert sample["pids"] == 12
