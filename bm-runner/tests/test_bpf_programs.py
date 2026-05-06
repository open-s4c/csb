# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import importlib
import inspect

from config.env_config import UniversalConfig
from monitors.bpf_parser import BPFParser
from monitors.bpf_program import BPFProgram
from monitors.bpf_program_factory import BPFProgramFactory, DummyBPFProgram
import monitors.bpftrace_programs as bpftrace_programs


def bpftrace_program_classes():
    classes = []
    for module_name in bpftrace_programs.__all__:
        module = importlib.import_module(f"monitors.bpftrace_programs.{module_name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BPFProgram) and obj is not BPFProgram and obj.__module__ == module.__name__:
                classes.append(obj)
    return classes


def test_all_bpftrace_program_descriptions_are_filterable():
    classes = bpftrace_program_classes()
    names = [cls.name for cls in classes]

    assert classes
    assert len(names) == len(set(names))

    for cls in classes:
        assert isinstance(cls.name, str) and cls.name
        assert isinstance(cls.program, str) and cls.program.strip()
        assert isinstance(cls.parser, BPFParser)

        program = cls(cls.parser, cls.name, dir="/tmp/results", args=["3", "42", "--unsafe"])
        filtered = program.get_program()

        assert "__FILTER_CPU__" not in filtered
        assert "__FILTER_PID__" not in filtered
        assert "cpu == 3" in filtered
        assert "pid == 42" in filtered
        assert program.args == ["--unsafe"]
        assert program.get_out_filename() == f"bpf_{cls.name}.log"
        assert program.get_csv_key() == cls.name


def test_bpf_program_filters_default_to_true():
    program = BPFProgram(
        parser=BPFParser(),
        name="example",
        dir="/tmp/results",
        args=[],
    )
    program.program = "/ __FILTER_CPU__ && __FILTER_PID__ / { @[pid] = count(); }"

    assert program.get_program() == "/ 1 && 1 / { @[pid] = count(); }"
    assert program.get_out_filename() == "bpf_example.log"
    assert program.get_csv_key() == "example"


def test_bpf_program_collect_results_delegates_to_parser(tmp_path):
    calls = []

    class FakeParser:
        @staticmethod
        def parse(filename):
            calls.append(("parse", filename))
            return {"rows": 1}

        @staticmethod
        def results_min_max_avg(df, PIDs, csv_key):
            calls.append(("minmax", df, PIDs, csv_key))
            return "metric_min=1;metric_avg=1;metric_max=1;"

        @staticmethod
        def results_histogram(df, PIDs, csv_key):
            calls.append(("histogram", df, PIDs, csv_key))
            return "metric_histogram=1;"

    program = BPFProgram(parser=FakeParser(), name="metric", dir=str(tmp_path), args=[])

    assert program.collect_results(str(tmp_path), PIDs=[7], csv_key="metric") == (
        "metric_min=1;metric_avg=1;metric_max=1;metric_histogram=1;"
    )
    assert calls == [
        ("parse", str(tmp_path / "bpf_metric.log")),
        ("minmax", {"rows": 1}, [7], "metric"),
        ("histogram", {"rows": 1}, [7], "metric"),
    ]


def test_program_factory_creates_named_program_and_deduplicates_discovery(monkeypatch, tmp_path):
    monkeypatch.delenv(UniversalConfig.CSB_ANALYZE.value, raising=False)
    BPFProgramFactory.progs = [BPFProgram]

    program = BPFProgramFactory.create("sched_fork", str(tmp_path), ["1", "123", "--flag"])

    assert program.name == "sched_fork"
    assert program.dir == str(tmp_path)
    assert program.cpu == 1
    assert program.pid == 123
    assert program.args == ["--flag"]
    assert "cpu == 1" in program.get_program()
    assert "pid == 123" in program.get_program()

    discovered_once = [prog.name for prog in BPFProgramFactory.progs]
    BPFProgramFactory.get_classes()
    discovered_twice = [prog.name for prog in BPFProgramFactory.progs]
    assert discovered_once == discovered_twice


def test_program_factory_returns_dummy_when_analysis_is_disabled(monkeypatch):
    monkeypatch.setenv(UniversalConfig.CSB_ANALYZE.value, "false")

    program = BPFProgramFactory.create("not_started", "/tmp/results", [])

    assert isinstance(program, DummyBPFProgram)
    assert program.name == "not_started"
    assert program.get_program() == ""
    assert program.collect_results("/tmp/results", PIDs=[1], csv_key="not_started") == ""
