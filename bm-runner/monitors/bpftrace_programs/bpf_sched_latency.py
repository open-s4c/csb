import os
from typing import Optional
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFSchedLatency(BPFProgram):
    program= """
tracepoint:sched:sched_wakeup,
tracepoint:sched:sched_wakeup_new
/ __FILTER_CPU__ && __FILTER_PID__ /
{
  @qtime[args.pid] = nsecs;
}

tracepoint:sched:sched_switch
/ __FILTER_CPU__ && __FILTER_PID__ /
{
  if (args.prev_state == TASK_RUNNING) {
    @qtime[args.prev_pid] = nsecs;
  }
  // Ignore the idle task
  if (args.next_pid == 0) {
    return;
  }

  $ns = @qtime[args.next_pid];
  if $ns {
    @usecs = hist((nsecs - $ns) / 1000);
    // Swallowing deletion failures as they are expected
    $ignore = delete(@qtime, args.next_pid);
  }
}

END
{
  clear(@qtime);
}
"""
    filename = "bpf_sched_latency.log"

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