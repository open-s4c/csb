import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFSchedLatency(BPFProgram):
    program= """
#ifndef BPFTRACE_HAVE_BTF                                                                                                                                                                                                                                                                           :(
#include <linux/sched.h>
#else
#define TASK_RUNNING 0
#endif
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
    @nsecs = hist(nsecs - $ns);
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
    csv_key = "sched_latency"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histogram(filepath)
        result += self.results_histogram_min_max_avg(df = df)
        result += self.results_histogram_histogram(df = df)
        return result
