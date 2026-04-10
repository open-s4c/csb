# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import subprocess
import threading
import signal
import pandas as pd
import matplotlib.pyplot as plt
import time
from monitors.monitor import Monitor
from monitors.bpf_program import BPFProgram
from monitors.bpf_program_factory import BPFProgramFactory
from bm_utils import ensure_exists
from utils.logger import bm_log, LogType
from typing import Optional

class BPFTraceCmd:
    def continue_writing(self, stream, filename):
        try:
            with open(filename, "w") as f:
                for line in stream:   # ← exits automatically on EOF
                    f.write(line)
                f.flush()
        finally:
            stream.close()  # optional, but clean

    def __init__(self, output_dir: str, ptype, output_file: str, program_str: str, cmd_args: list[str]):
        # begin_signal = 'BEGIN { printf("PROBE_READY"); }\n'
        self.fname = os.path.join(output_dir, output_file)
        cmds = ["sudo", "bpftrace", "-e"]
        cmds.append(f"{program_str}")
        cmds.extend(cmd_args)
        cmd_str = " ".join(cmds)
        # print(f"Running command {cmd_str}")
        env = {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
        bm_log(f"Running bpftrace with {ptype}")
        self.process = subprocess.Popen(cmds, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setpgrp, text=True, bufsize=1)
        self.out_thread = threading.Thread(
            target=self.continue_writing,
            args=(self.process.stdout, self.fname),
            daemon=True
        )
        for line in self.process.stdout:
            # print(f"bpftrace output: {line}")
            if "Attach" in line and "probe" in line:
                self.out_thread.start()
                while not self.out_thread.is_alive():
                    time.sleep(0.1)
                break

    def stop(self):
        # This acts like ctrl+C
        self.process.send_signal(signal.SIGINT)
        # print("Waiting for bpftrace monitor to stop.")
        self.process.wait()
        if self.out_thread.is_alive():
            self.out_thread.join()

class BPFTraceStats(Monitor):
    programs: dict[str, (BPFProgram, BPFTraceCmd)] = {}
    def __init__(self, output_dir: str, args: dict[list[str]]):
        ensure_exists("bpftrace")
        for program_name in args:
            # ptype = BPFProgramType[programtype]
            prog = BPFProgramFactory.create(program_name, output_dir, args[program_name])
            self.programs[program_name] = (prog, None)
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
            result_local = prog.collect_results(self.dir, PIDs=pids, csv_key=prog.get_csv_key())
            # bm_log(f"Result from {progtype}:\n{result_local}\n", LogType.FATAL)

            result += result_local
        return result
