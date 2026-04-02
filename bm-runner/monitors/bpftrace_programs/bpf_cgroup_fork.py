import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFCGroupFork(BPFProgram):
    program = """
kprobe:cgroup_can_fork,
kprobe:cgroup_fork 
/ __FILTER_CPU__ && __FILTER_PID__ /
{
    @start[tid] = nsecs;
}
kretprobe:cgroup_can_fork,
kretprobe:cgroup_fork /@start[tid]/ {
    $duration = (nsecs - @start[tid]) / 1000;
    @fork_latency = hist($duration);
    delete(@start[tid]);
}
"""
    filename = "bpf_cgroup_fork.log"
    csv_key = "cgroup_fork"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histogram(filepath)
        result += self.results_histogram_min_max_avg(df=df)
        result += self.results_histogram_histogram(df=df)
        return result
