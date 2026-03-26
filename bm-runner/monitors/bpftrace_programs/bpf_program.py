# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Optional

class BPFProgram:
    program = ""
    cpu = -1
    pid = -1

    def __init__(self, dir, args):
        self.dir = dir
        self.args = args[3:]
        self.progname = args[0]
        self.cpu = int(args[1])
        self.pid = int(args[2])

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

    def gen_program(self) -> str:
        return self.apply_filters(self.program)

    @abstractmethod
    def get_program(self) -> str:
        pass

    @abstractmethod
    def get_out_filename(self) -> str:
        pass

    @abstractmethod
    def collect_results(self, output_dir: str) -> Optional[dict]:
        pass
