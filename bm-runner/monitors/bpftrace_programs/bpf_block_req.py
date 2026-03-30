import os
import pandas as pd
from monitors.bpftrace_programs.bpf_program import BPFProgram

class BPFBlockReq(BPFProgram):
    program = """
tracepoint:block:block_rq_complete
/ __FILTER_CPU__ && __FILTER_PID__ /
{ @requests[pid] = hist(args->nr_sector * 512) }
"""
    filename = "bpf_block_req.log"
    csv_key = "block_req"

    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        filepath = os.path.join(output_dir, self.filename)
        df = self.parse_histograms(filepath)
        result = self.results_histograms(df=df, PIDs = PIDs)
        return result
