# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import io
import signal
import subprocess

import pandas as pd

import monitors.bpftrace as bpftrace_module
from monitors.bpftrace import BPFTraceCmd, BPFTraceStats


def test_bpftrace_cmd_continue_writing_copies_stream_and_closes(tmp_path):
    stream = io.StringIO("line-1\nline-2\n")
    output = tmp_path / "bpf.log"

    cmd = BPFTraceCmd.__new__(BPFTraceCmd)
    cmd.continue_writing(stream, output)

    assert output.read_text() == "line-1\nline-2\n"
    assert stream.closed


def test_bpftrace_cmd_builds_command_and_stops_process(monkeypatch, tmp_path):
    captured = {}

    class FakeProcess:
        def __init__(self):
            self.stdout = iter(["Attaching 1 probe...\n"])
            self.sent_signal = None
            self.waited = False

        def send_signal(self, sent_signal):
            self.sent_signal = sent_signal

        def wait(self):
            self.waited = True

    class FakeThread:
        instances = []

        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon
            self.started = False
            self.joined = False
            self._alive = False
            FakeThread.instances.append(self)

        def start(self):
            self.started = True
            self._alive = True

        def is_alive(self):
            return self._alive

        def join(self):
            self.joined = True
            self._alive = False

    def fake_popen(cmds, **kwargs):
        process = FakeProcess()
        captured["cmds"] = cmds
        captured["kwargs"] = kwargs
        captured["process"] = process
        return process

    monkeypatch.setattr(bpftrace_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(bpftrace_module.threading, "Thread", FakeThread)

    cmd = BPFTraceCmd(
        output_dir=str(tmp_path),
        ptype="sched_fork",
        output_file="bpf_sched_fork.log",
        program_str="tracepoint:sched:sched_process_fork { @[pid] = count(); }",
        cmd_args=["--unsafe", "-D", "flag=1"],
    )

    assert captured["cmds"] == [
        "sudo",
        "bpftrace",
        "-e",
        "tracepoint:sched:sched_process_fork { @[pid] = count(); }",
        "--unsafe",
        "-D",
        "flag=1",
    ]
    assert captured["kwargs"]["env"] == {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
    assert captured["kwargs"]["stdin"] == subprocess.DEVNULL
    assert captured["kwargs"]["stdout"] == subprocess.PIPE
    assert captured["kwargs"]["stderr"] == subprocess.STDOUT
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["bufsize"] == 1
    assert cmd.fname == str(tmp_path / "bpf_sched_fork.log")
    assert FakeThread.instances[0].args == (captured["process"].stdout, cmd.fname)
    assert FakeThread.instances[0].daemon is True
    assert FakeThread.instances[0].started is True

    cmd.stop()

    assert captured["process"].sent_signal == signal.SIGINT
    assert captured["process"].waited is True
    assert FakeThread.instances[0].joined is True


def test_bpftrace_stats_lifecycle_uses_program_factory_and_collects(monkeypatch, tmp_path):
    ensure_exists_calls = []
    created_programs = {}

    class FakeProgram:
        def __init__(self, name, args):
            self.name = name
            self.args = [f"--{name}"]
            self.input_args = args
            self.collect_calls = []

        def get_out_filename(self):
            return f"bpf_{self.name}.log"

        def get_program(self):
            return f"program for {self.name}"

        def get_csv_key(self):
            return f"csv_{self.name}"

        def collect_results(self, output_dir, PIDs, csv_key):
            self.collect_calls.append((output_dir, PIDs, csv_key))
            return f"{csv_key}=ok;"

    class FakeBPFTraceCmd:
        instances = []

        def __init__(self, output_dir, ptype, output_file, program_str, cmd_args):
            self.output_dir = output_dir
            self.ptype = ptype
            self.output_file = output_file
            self.program_str = program_str
            self.cmd_args = cmd_args
            self.stopped = False
            FakeBPFTraceCmd.instances.append(self)

        def stop(self):
            self.stopped = True

    def fake_ensure_exists(name):
        ensure_exists_calls.append(name)
        return name

    def fake_create(program_name, results_dir, args):
        program = FakeProgram(program_name, args)
        created_programs[program_name] = program
        assert results_dir == str(tmp_path)
        return program

    monkeypatch.setattr(bpftrace_module, "ensure_exists", fake_ensure_exists)
    monkeypatch.setattr(bpftrace_module.BPFProgramFactory, "create", staticmethod(fake_create))
    monkeypatch.setattr(bpftrace_module, "BPFTraceCmd", FakeBPFTraceCmd)

    monitor = BPFTraceStats(str(tmp_path), {"sched_fork": ["1"], "block_req": ["2", "3"]})

    assert ensure_exists_calls == ["bpftrace"]
    assert set(monitor.programs) == {"sched_fork", "block_req"}

    monitor.start()

    assert [(cmd.ptype, cmd.output_file, cmd.program_str, cmd.cmd_args) for cmd in FakeBPFTraceCmd.instances] == [
        ("sched_fork", "bpf_sched_fork.log", "program for sched_fork", ["--sched_fork"]),
        ("block_req", "bpf_block_req.log", "program for block_req", ["--block_req"]),
    ]

    monitor.stop()
    assert all(cmd.stopped for cmd in FakeBPFTraceCmd.instances)

    assert monitor.collect_results([101, 202]) == "csv_sched_fork=ok;csv_block_req=ok;"
    assert created_programs["sched_fork"].collect_calls == [(str(tmp_path), [101, 202], "csv_sched_fork")]
    assert created_programs["block_req"].collect_calls == [(str(tmp_path), [101, 202], "csv_block_req")]


def test_bpftrace_stats_programs_are_instance_local(monkeypatch, tmp_path):
    monkeypatch.setattr(bpftrace_module, "ensure_exists", lambda name: name)

    class FakeProgram:
        def __init__(self, name):
            self.name = name
            self.args = []

    def fake_create(program_name, results_dir, args):
        return FakeProgram(program_name)

    monkeypatch.setattr(bpftrace_module.BPFProgramFactory, "create", staticmethod(fake_create))

    first = BPFTraceStats(str(tmp_path / "first"), {"sched_fork": []})
    second = BPFTraceStats(str(tmp_path / "second"), {"block_req": []})

    assert set(first.programs) == {"sched_fork"}
    assert set(second.programs) == {"block_req"}


def test_bpftrace_stats_dataframe_to_keyvalue_csv():
    monitor = BPFTraceStats.__new__(BPFTraceStats)
    df = pd.DataFrame({"metric": ["a", "b"], "min": [1, 2], "max": [3, 4]})

    assert monitor.dataframe_to_keyvalue_csv(df) == "a=1|3;b=2|4;"
