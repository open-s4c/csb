import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFSchedFork(BPFProgram):
    program = """
tracepoint:sched:sched_process_fork
/ __FILTER_CPU__ && __FILTER_PID__ /
{ @[args->parent_pid] = count(); }
"""
    filename = "bpf_sched_fork.log"
    csv_key = "sched_fork_count"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_counts(filepath)
        result += self.results_counts_min_max_avg(df=df, PIDs = PIDs)
        return result
