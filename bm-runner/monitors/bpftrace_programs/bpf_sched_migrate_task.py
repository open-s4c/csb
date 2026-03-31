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
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_counts(filepath)
        # print(df)
        result = self.results_counts(df=df, PIDs = PIDs)
        return result
