# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFCGroupCharge(BPFProgram):
    program = """
kprobe:__mem_cgroup_charge 
/ __FILTER_CPU__ && __FILTER_PID__ /
{
    @start[tid] = nsecs;
}
kretprobe:__mem_cgroup_charge /@start[tid]/ {
    $duration = (nsecs - @start[tid]) / 1000;
    @charge_latency = hist($duration);
    delete(@start[tid]);
}
"""
    filename = "bpf_cgroup_charge.log"
    csv_key = "cgroup_charge"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histogram(filepath)
        result += self.results_histogram_min_max_avg(df=df)
        result += self.results_histogram_histogram(df=df)
        return result
