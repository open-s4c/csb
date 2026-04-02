import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFSchedDomainsMutex(BPFProgram):
    program = """
kprobe:sched_domains_mutex_lock
/ __FILTER_CPU__ && __FILTER_PID__ /
{
    @start[tid] = nsecs;
}
kretprobe:sched_domains_mutex_lock
/ @start[tid] /
{
    $wait_ns = nsecs - @start[tid];
    @wait_time[pid] = hist($wait_ns);
    delete(@start[tid]);
}
END {
    print(@wait_time);
}
"""
    filename = "bpf_sched_domains_mutex.log"
    csv_key = "sched_domains_mutex"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histograms(filepath)
        result += self.results_histograms_min_max_avg(df=df, PIDs = PIDs)
        result += self.results_histograms_histogram(df=df, PIDs = PIDs)
        return result
