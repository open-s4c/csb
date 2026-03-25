# bpftrace -e 

from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFSchedFork(BPFProgram):
    program = 'tracepoint:sched:sched_process_fork { @[args->parent_comm, args->child_comm] = count(); }'
    filename = "bpf_sched_fork.log"

    def __init__(self, dir: str, cmd_args: list[str]):
        super().__init__(dir=dir, args=cmd_args)

    def get_program(self):
        return self.program

    def get_out_filename(self):
        return self.filename

    def collect_results(self):
        return "todo"