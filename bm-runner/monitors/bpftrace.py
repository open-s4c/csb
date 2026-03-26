# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import subprocess
import signal
import pandas as pd
import matplotlib.pyplot as plt
from monitors.monitor import Monitor
from monitors.bpftrace_programs.bpf_program_factory import BPFProgramFactory,BPFProgramType
from bm_utils import ensure_exists
from utils.logger import bm_log, LogType
from typing import Optional

class BPFTraceCmd:
    def __init__(self, output_dir: str, output_file: str, program_str: str, cmd_args: list[str]):
        self.fname = os.path.join(output_dir, output_file)
        cmds = ["sudo", "bpftrace", "-o", self.fname, "-e"]
        cmds.append(f"{program_str}")
        cmds.extend(cmd_args)
        cmd_str = " ".join(cmds)
        env = {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
        bm_log(f"Running {cmd_str}")
        self.process = subprocess.Popen(cmds, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop(self):
        # This acts like ctrl+C
        self.process.send_signal(signal.SIGINT)


class BPFTraceStats(Monitor):

    def __init__(self, output_dir: str, args: list[str]):
        ensure_exists("bpftrace")
        self.program = BPFProgramFactory.create(BPFProgramType[args[0]], output_dir, args)
        super().__init__(dir=output_dir, args=args)
        self.stat: Optional[BPFTraceCmd] = None

    def start(self):
        self.stat = BPFTraceCmd(self.dir, self.program.get_out_filename(), self.program.get_program(), self.program.args)

    def stop(self):
        if self.stat is not None:
            self.stat.stop()

    def collect_results(self) -> str:
        if self.program:
            data = self.program.collect_results(self.dir)
            if data:
                result = "\n".join(data)
                return result
        else:
            bm_log(
                f"Could not read output of bpftrace {self.args[0]}, `self.program` is not initialized!", LogType.ERROR
            )
        return ""

