import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFCGroupRstatLockCont(BPFProgram):
    program = """

tracepoint:cgroup:cgroup_rstat_lock_contended
/ __FILTER_CPU__ && __FILTER_PID__ /
{
    @contended[pid] = count();
}
"""
    filename = "bpf_cgroup_rstat_lock_cont.log"
    csv_key = "cgroup_rstat_lock_cont"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_counts(filepath)
        result = self.results_counts(df=df, PIDs = PIDs)
        return result
