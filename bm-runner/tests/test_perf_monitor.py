# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from monitors.perf import FlameGraph


def test_arm_spe_event_uses_env_period(monkeypatch):
    monkeypatch.setenv(FlameGraph.ARM_SPE_PERIOD_ENV_VAR_NAME, "20480")

    assert FlameGraph.arm_spe_event() == "arm_spe/jitter=1,period=20480/"


def test_arm_spe_event_uses_ten_times_sysfs_min_interval(monkeypatch, tmp_path):
    min_interval = tmp_path / "arm_spe_0" / "caps" / "min_interval"
    min_interval.parent.mkdir(parents=True)
    min_interval.write_text("1024")
    monkeypatch.delenv(FlameGraph.ARM_SPE_PERIOD_ENV_VAR_NAME, raising=False)
    monkeypatch.setattr(
        FlameGraph,
        "ARM_SPE_MIN_INTERVAL_GLOB",
        str(tmp_path / "arm_spe*" / "caps" / "min_interval"),
    )

    assert FlameGraph.arm_spe_event() == "arm_spe/jitter=1,period=10240/"


def test_perf_events_skip_arm_spe_when_sysfs_device_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(FlameGraph, "ARM_SPE_DEVICE_GLOB", str(tmp_path / "arm_spe*"))
    monkeypatch.setenv(FlameGraph.ARM_SPE_PERIOD_ENV_VAR_NAME, "not-an-int")

    assert FlameGraph.perf_events() == ["cycles"]
    assert FlameGraph.perf_record_cmd(["-a"]) == [
        "sudo",
        "perf",
        "record",
        "--kcore",
        "-g",
        "-e",
        "cycles",
        "-a",
    ]


def test_perf_events_include_arm_spe_when_sysfs_device_has_type(monkeypatch, tmp_path):
    min_interval = tmp_path / "arm_spe_0" / "caps" / "min_interval"
    min_interval.parent.mkdir(parents=True)
    min_interval.write_text("1024")
    (tmp_path / "arm_spe_0" / "type").write_text("999")
    monkeypatch.delenv(FlameGraph.ARM_SPE_PERIOD_ENV_VAR_NAME, raising=False)
    monkeypatch.setattr(FlameGraph, "ARM_SPE_DEVICE_GLOB", str(tmp_path / "arm_spe*"))
    monkeypatch.setattr(
        FlameGraph,
        "ARM_SPE_MIN_INTERVAL_GLOB",
        str(tmp_path / "arm_spe*" / "caps" / "min_interval"),
    )

    assert FlameGraph.perf_events() == ["cycles", "arm_spe/jitter=1,period=10240/"]
    assert FlameGraph.perf_record_cmd(["-a"]) == [
        "sudo",
        "perf",
        "record",
        "--kcore",
        "-g",
        "-e",
        "cycles",
        "-e",
        "arm_spe/jitter=1,period=10240/",
        "-a",
    ]
