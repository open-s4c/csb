# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFCGroupRstatFlush(BPFProgram):
    program = """
kprobe:mem_cgroup_css_rstat_flush
/ __FILTER_CPU__ && __FILTER_PID__ /
{
    @start[tid] = nsecs;
}
kretprobe:mem_cgroup_css_rstat_flush /@start[tid]/ {
    $duration = (nsecs - @start[tid]) / 1000;
    @flush_latency = hist($duration);
    delete(@start[tid]);
}
"""
    filename = "bpf_cgroup_rstat_flush.log"
    csv_key = "cgroup_rstat_flush"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histogram(filepath)
        result += self.results_histogram_min_max_avg(df=df)
        result += self.results_histogram_histogram(df=df)
        return result
