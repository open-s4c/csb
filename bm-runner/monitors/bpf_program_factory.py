# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import sys, inspect
from enum import Enum

from utils.logger import bm_log, LogType
from config.env_config import EnvUniversalConfig, UniversalConfig

from monitors.bpf_program import BPFProgram
from monitors.bpf_parser import BPFParser
from monitors.bpftrace_programs import *

class DummyBPFProgram(BPFProgram):
    def __init__(self, name: str):
        super().__init__(parser=BPFParser(), name=name, dir="", args=[])

    def get_program(self):
        bm_log(
            f"Requested bpf_program `{self.name}` from config is not started, since environment variable `{UniversalConfig.CSB_ANALYZE}` "
            f"is set to `false`."
            f"To reactivate bpf_programs remove `{UniversalConfig.CSB_ANALYZE}` or set it to `true`",
            LogType.WARNING,
        )
        return ""

    def collect_results(self, *args, **kwargs) -> str:
        return ""

class BPFProgramFactory:
    progs = [BPFProgram]

    @staticmethod
    def get_classes():
        progs = [BPFProgram]
        for module_name, module in list(sys.modules.items()):
            if module_name.__contains__(".bpftrace_programs."):
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BPFProgram)
                        and obj is not BPFProgram
                        and obj.__module__.__contains__(".bpftrace_programs.")
                    ):
                        progs.append(obj)
        BPFProgramFactory.progs = sorted(
            progs,
            key=lambda prog: getattr(prog, "name", ""),
        )

    @staticmethod
    def create(bpf_program_name: str, results_dir, args) -> BPFProgram:
        BPFProgramFactory.get_classes()
        # if the user has requested to disable the monitors,
        # we return a dummy monitor that does nothing,
        # so that the rest of the code can remain unchanged
        # print(f"Matching bpf program {bpf_program_name}")
        if not EnvUniversalConfig.is_on(UniversalConfig.CSB_ANALYZE):
            return DummyBPFProgram(bpf_program_name)  # Return a dummy bpf_program that does nothing
        
        for prog in BPFProgramFactory.progs:
            # print(f"Matching {bpf_program_name} against {getattr(prog, "name")}")
            if bpf_program_name == getattr(prog, "name"):
                return prog(getattr(prog, "parser"), bpf_program_name, dir=results_dir, args=args)

        bm_log(f"Unsupported bpf_program type {bpf_program_name}", LogType.FATAL)
        sys.exit(1)
