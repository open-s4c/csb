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

    def __init__(self, name:str, dir: str, cmd_args: list[str]):
        super().__init__(name=name, dir=dir, args=cmd_args)

    def get_program(self):
        program = self.gen_program()
        return program

    def get_out_filename(self):
        return self.filename

    def collect_results(self, output_dir: str) -> pd.DataFrame:
        filepath = os.path.join(output_dir, self.filename)
        return self.parse_histograms(filepath)
