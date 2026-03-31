# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import subprocess
import signal
import pandas as pd
import matplotlib.pyplot as plt
from monitors.monitor import Monitor
from monitors.bpftrace_programs.bpf_program import BPFProgram
from monitors.bpftrace_programs.bpf_program_factory import BPFProgramFactory,BPFProgramType
from bm_utils import ensure_exists
from utils.logger import bm_log, LogType
from typing import Optional

class BPFTraceCmd:
    def __init__(self, output_dir: str, ptype, output_file: str, program_str: str, cmd_args: list[str]):
        self.fname = os.path.join(output_dir, output_file)
        cmds = ["sudo", "bpftrace", "-o", self.fname, "-e"]
        cmds.append(f"{program_str}")
        cmds.extend(cmd_args)
        cmd_str = " ".join(cmds)
        env = {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
        bm_log(f"Running bpftrace with {BPFProgramType[ptype]}")
        self.process = subprocess.Popen(cmds, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)

    def stop(self):
        # This acts like ctrl+C
        self.process.send_signal(signal.SIGINT)
        self.process.wait()

class BPFTraceStats(Monitor):
    programs: dict[BPFProgramType, (BPFProgram, BPFTraceCmd)] = {}
    def __init__(self, output_dir: str, args: dict[list[str]]):
        ensure_exists("bpftrace")
        for programtype in args:
            ptype = BPFProgramType[programtype]
            prog = BPFProgramFactory.create(ptype, output_dir, args[programtype])
            self.programs[ptype] = (prog, None)
        super().__init__(dir=output_dir, args=args)

    def start(self):
        for ptype, (prog, stat) in self.programs.items():
            stat = BPFTraceCmd(self.dir, ptype, prog.get_out_filename(), prog.get_program(), prog.args)
            self.programs[ptype] = (prog, stat)

    def stop(self):
        for ptype, (prog, stat) in self.programs.items():
            if stat is not None:
                stat.stop()

    # Function to process the DataFrame
    def dataframe_to_keyvalue_csv(self, df, value_delimiter='|') ->str:
        # Ensure first column is the key
        key_col = df.columns[0]
        value_cols = df.columns[1:]
        
        # Concatenate the value columns with delimiter
        df['values'] = df[value_cols].astype(str).agg(value_delimiter.join, axis=1)
        
        # Create the CSV string with just key and concatenated value
        csv_str = df[[key_col, 'values']].to_csv(index=False, header=False, sep='=').replace('\n', ';')
        
        return csv_str
    
    def collect_results(self, pids: Optional[list[int]]) -> str:
        result=""
        for progtype, (prog, stat) in self.programs.items():
            result_local = prog.collect_results(self.dir, PIDs=pids)
            # bm_log(f"Result from {progtype}:\n{result_local}\n", LogType.FATAL)

            result += result_local
        return result
