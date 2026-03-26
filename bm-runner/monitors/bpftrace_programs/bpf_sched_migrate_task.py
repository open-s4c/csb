import os
from typing import Optional
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFSchedMigrateTask(BPFProgram):
    program = "tracepoint:sched:sched_migrate_task / __FILTER_CPU__ && __FILTER_PID__ / {@migrations[pid] = count();}"
    filename = "bpf_sched_migrate_task.log"

    def __init__(self, name:str, dir: str, cmd_args: list[str]):
        super().__init__(name=name, dir=dir, args=cmd_args)

    def get_program(self):
        program = self.gen_program()
        return program

    def get_out_filename(self):
        return self.filename

    def collect_results(self, output_dir: str) -> Optional[dict]:
        filepath = os.path.join(output_dir, self.filename)
        with open(filepath, "r") as fp:
            return fp.read()
        return "todo"