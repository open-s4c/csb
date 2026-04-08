# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from monitors.bpf_parser import BPFParser
import os

class BPFProgram:
    parser:BPFParser
    name = ""
    description = ""
    program = ""
    cpu = -1
    pid = -1

    def __init__(self, parser, name, dir, args):
        self.parser = parser
        self.dir = dir
        self.args = args[2:]
        self.progname = name
        self.cpu = int(args[0])
        self.pid = int(args[1])

    def _filter_cpu(self, program:str) -> str:
        if self.cpu >= 0:
            return program.replace("__FILTER_CPU__", f"cpu == {self.cpu}")
        else:
            return program.replace("__FILTER_CPU__", "1")
        
    def _filter_pid(self, program:str) -> str:
        if self.pid >= 1:
            return program.replace("__FILTER_PID__", f"pid == {self.pid}")
        else:
            return program.replace("__FILTER_PID__", "1")

    def apply_filters(self, program:str) -> str:
        filtered_program = program
        filtered_program = self._filter_cpu(filtered_program)
        filtered_program = self._filter_pid(filtered_program)
        return filtered_program

    def get_program(self) -> str:
        return self.apply_filters(self.program)

    def get_out_filename(self):
        return f"bpf_{self.name}.log"

    def get_csv_key(self):
        return f"{self.name}"

    def collect_results(self, output_dir: str, PIDs: list[int], csv_key: str) -> str:
        result = ""
        filepath = os.path.join(output_dir, self.get_out_filename())
        df = self.parser.parse(filepath)
        result += self.parser.results_min_max_avg(df=df, PIDs = PIDs, csv_key=csv_key)
        result += self.parser.results_histogram(df=df, PIDs = PIDs, csv_key=csv_key)
        return result
