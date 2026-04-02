import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFSchedMigrateTask(BPFProgram):
    program = """
tracepoint:sched:sched_migrate_task
/ __FILTER_CPU__ && __FILTER_PID__ /
{@migrations[pid] = count();}
"""

    filename = "bpf_sched_migrate_task.log"
    csv_key = "sched_migrate"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_counts(filepath)
        result += self.results_counts_min_max_avg(df=df, PIDs = PIDs)
        return result
