# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFExt4MbNewBLocks(BPFProgram):
    program = """
kprobe:ext4_mb_new_blocks 
/ __FILTER_CPU__ && __FILTER_PID__ /
{ @start[pid] = nsecs; }

kretprobe:ext4_mb_new_blocks 
/ @start[pid] /
{ @ns[pid] = hist(nsecs - @start[pid]); delete(@start[pid]); }
"""
    csv_key = "ext4_mb_new_blocks"
    filename = f"bpf_{csv_key}.log"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histograms(filepath)
        result += self.results_histograms_histogram(df=df, PIDs = PIDs)
        return result
