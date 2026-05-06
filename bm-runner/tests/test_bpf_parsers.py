# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import pytest
import pandas as pd

from monitors.bpf_parser import BPFParser
from monitors.bpf_parser_counts import BPFParserCounts
from monitors.bpf_parser_helper import BPFParserHelper
from monitors.bpf_parser_histogram import BPFParserHistogram
from monitors.bpf_parser_histograms import BPFParserHistograms


def parse_key_values(result: str) -> dict[str, str]:
    return dict(item.split("=") for item in result.strip(";").split(";") if item)


def parse_histogram(result: str, csv_key: str) -> list[int]:
    prefix = f"{csv_key}_histogram="
    assert result.startswith(prefix)
    assert result.endswith(";")
    return [int(value) for value in result[len(prefix) : -1].split(",")]


def test_default_results_are_stable():
    assert BPFParser.default_min_max_avg("metric") == "metric_min=0;metric_avg=0;metric_max=0;"

    histogram = parse_histogram(BPFParser.default_histogram("metric"), "metric")
    assert histogram == [0] * 60


def test_range_helper_handles_unit_suffixes():
    assert BPFParserHelper.symbol_to_factor("") == 1
    assert BPFParserHelper.symbol_to_factor("K") == 1000
    assert BPFParserHelper.symbol_to_factor("M") == 1000000
    assert BPFParserHelper.symbol_to_factor("G") == 1000000000
    assert BPFParserHelper.symbol_to_factor("T") == 1000000000000
    assert BPFParserHelper.symbol_to_factor("P") == 1000000000000000
    assert BPFParserHelper.get_range_max("[512, 1K)") == 999
    assert BPFParserHelper.get_range_avg("[512, 1K)") == 756
    assert BPFParserHelper.get_range_avg("[1K, 2M)") == 1000500


def test_range_helper_returns_zero_for_invalid_ranges():
    assert BPFParserHelper.get_range_max("not a range") == 0
    assert BPFParserHelper.get_range_avg("not a range") == 0


def test_counts_parser_parses_count_maps_and_filters_pids(tmp_path):
    output = tmp_path / "counts.log"
    output.write_text("@[123]: 7\n@[456]: 2\n")

    df = BPFParserCounts.parse(output)

    assert df.to_dict("records") == [
        {"PID": 123, "Count": 7},
        {"PID": 456, "Count": 2},
    ]
    assert (
        BPFParserCounts.results_min_max_avg(df, PIDs=[123], csv_key="sched_fork")
        == "sched_fork_min=7;sched_fork_avg=7.0;sched_fork_max=7;"
    )
    assert (
        BPFParserCounts.results_min_max_avg(df, PIDs=[], csv_key="sched_fork")
        == "sched_fork_min=2;sched_fork_avg=4.5;sched_fork_max=7;"
    )
    assert (
        BPFParserCounts.results_min_max_avg(df, PIDs=[999], csv_key="sched_fork")
        == BPFParser.default_min_max_avg("sched_fork")
    )
    assert BPFParserCounts.results_histogram(df, PIDs=[123], csv_key="sched_fork") == BPFParser.default_histogram(
        "sched_fork"
    )


def test_counts_parser_returns_empty_dataframe_for_bpftrace_errors(tmp_path):
    output = tmp_path / "counts.log"
    output.write_text("ERROR: cannot attach probe, entry may not exist\n")

    assert BPFParserCounts.parse(output).empty
    output.write_text("\n   \n")
    assert BPFParserCounts.parse(output).empty
    assert BPFParserCounts.parse(tmp_path / "missing.log").empty


def test_histograms_parser_parses_per_pid_histograms_and_filters_results(tmp_path):
    output = tmp_path / "histograms.log"
    output.write_text(
        "\n".join(
            [
                "@ns[123]:",
                "[1, 2) 3 |@@@",
                "[2, 4) 1 |@",
                "@ns[999]:",
                "[8, 16) 5 |@@@@@",
            ]
        )
    )

    df = BPFParserHistograms.parse(output)

    assert df.to_dict("records") == [
        {"pid": 123, "range": "[1, 2)", "count": 3},
        {"pid": 123, "range": "[2, 4)", "count": 1},
        {"pid": 999, "range": "[8, 16)", "count": 5},
    ]

    key_values = parse_key_values(BPFParserHistograms.results_min_max_avg(df, PIDs=[123], csv_key="latency"))
    assert float(key_values["latency_min"]) == pytest.approx(1.5)
    assert float(key_values["latency_avg"]) == pytest.approx(1.875)
    assert float(key_values["latency_max"]) == pytest.approx(3.0)

    histogram = parse_histogram(BPFParserHistograms.results_histogram(df, PIDs=[123], csv_key="latency"), "latency")
    assert len(histogram) == 60
    assert histogram[0] == 4
    assert sum(histogram) == 4

    assert (
        BPFParserHistograms.results_min_max_avg(df, PIDs=[321], csv_key="latency")
        == BPFParser.default_min_max_avg("latency")
    )
    assert BPFParserHistograms.results_histogram(df, PIDs=[321], csv_key="latency") == BPFParser.default_histogram(
        "latency"
    )


def test_histograms_parser_keeps_pid_zero_and_skips_ranges_before_pid(tmp_path):
    output = tmp_path / "histograms.log"
    output.write_text("\n".join(["[1, 2) 9 |@@@@@@@@@", "@ns[0]:", "[2, 4) 3 |@@@"]))

    df = BPFParserHistograms.parse(output)

    assert df.to_dict("records") == [{"pid": 0, "range": "[2, 4)", "count": 3}]
    assert (
        BPFParserHistograms.results_min_max_avg(df, PIDs=[0], csv_key="latency")
        == "latency_min=3.0;latency_avg=3.0;latency_max=3.0;"
    )


def test_histograms_results_default_when_all_counts_or_pids_are_filtered_out():
    df = BPFParserHistograms.parse(__file__)
    assert df.empty

    df = pd.DataFrame(
        [
            {"pid": 1, "range": "[1, 2)", "count": 0},
            {"pid": 2, "range": "[2, 4)", "count": 5},
        ]
    )

    assert (
        BPFParserHistograms.results_min_max_avg(df, PIDs=[1], csv_key="latency")
        == BPFParser.default_min_max_avg("latency")
    )
    assert BPFParserHistograms.results_histogram(df, PIDs=[1], csv_key="latency") == BPFParser.default_histogram(
        "latency"
    )


def test_histogram_parser_parses_global_histogram_results(tmp_path):
    output = tmp_path / "histogram.log"
    output.write_text("\n".join(["@latency:", "[0, 1) 2 |@@", "[1K, 2K) 1 |@"]))

    df = BPFParserHistogram.parse(output)

    assert df.to_dict("records") == [
        {"range": "[0, 1)", "count": 2},
        {"range": "[1K, 2K)", "count": 1},
    ]

    key_values = parse_key_values(BPFParserHistogram.results_min_max_avg(df, PIDs=[], csv_key="latency"))
    assert float(key_values["latency_min"]) == pytest.approx(0.5)
    assert float(key_values["latency_avg"]) == pytest.approx((0.5 * 2 + 1500 * 1) / 3)
    assert float(key_values["latency_max"]) == pytest.approx(1500.0)

    histogram = parse_histogram(BPFParserHistogram.results_histogram(df, PIDs=[], csv_key="latency"), "latency")
    assert len(histogram) == 60
    assert histogram[0] == 2
    assert histogram[9] == 1
    assert sum(histogram) == 3


def test_histogram_results_skip_zero_counts_and_cap_overflow_bucket():
    df = pd.DataFrame(
        [
            {"range": "[1, 2)", "count": 0},
            {"range": "[1P, 10000P)", "count": 4},
        ]
    )

    key_values = parse_key_values(BPFParserHistogram.results_min_max_avg(df, PIDs=[], csv_key="latency"))
    assert float(key_values["latency_min"]) == pytest.approx(5000500000000000000)
    assert float(key_values["latency_avg"]) == pytest.approx(5000500000000000000)
    assert float(key_values["latency_max"]) == pytest.approx(5000500000000000000)

    histogram = parse_histogram(BPFParserHistogram.results_histogram(df, PIDs=[], csv_key="latency"), "latency")
    assert histogram[-1] == 4
    assert sum(histogram) == 4
