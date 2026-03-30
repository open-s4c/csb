import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFVfsReadLatency(BPFProgram):
    program = """
kprobe:vfs_read 
/ __FILTER_CPU__ && __FILTER_PID__ /
{ @start[pid] = nsecs; }

kretprobe:vfs_read 
/ @start[pid] /
{ @ns[pid] = hist(nsecs - @start[pid]); delete(@start[pid]); }
"""
    filename = "bpf_sched_fork.log"
    csv_key = "sched_latency"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histograms(filepath)
        result = self.results_histograms(df = df, PIDs = PIDs)
        return result
