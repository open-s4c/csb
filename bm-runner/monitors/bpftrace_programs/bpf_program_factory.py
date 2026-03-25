import sys
from enum import Enum

from utils.logger import bm_log, LogType
from config.env_config import EnvUniversalConfig, UniversalConfig

from monitors.bpftrace_programs.bpf_program import BPFProgram
from monitors.bpftrace_programs.bpf_sched_fork import BPFSchedFork

class DummyBPFProgram(BPFProgram):
    def __init__(self, name: str):
        super().__init__(dir="", args=[])
        self.name = name

    def get_program(self):
        bm_log(
            f"Requested bpf_program `{self.name}` from config is not started, since environment variable `{UniversalConfig.CSB_ANALYZE}` "
            f"is set to `false`."
            f"To reactivate bpf_programs remove `{UniversalConfig.CSB_ANALYZE}` or set it to `true`",
            LogType.WARNING,
        )
        return ""

    def collect_results(self) -> str:
        return ""


class BPFProgramType(str, Enum):
    sched_fork = "sched_fork"

class BPFProgramFactory:
    @staticmethod
    def create(bpf_program_type: BPFProgramType, results_dir, args) -> BPFProgram:
        # if the user has requested to disable the monitors,
        # we return a dummy monitor that does nothing,
        # so that the rest of the code can remain unchanged
        if not EnvUniversalConfig.is_on(UniversalConfig.CSB_ANALYZE):
            return DummyBPFProgram(name=f"{bpf_program_type}")  # Return a dummy bpf_program that does nothing
        match bpf_program_type:
            case BPFProgramType.sched_fork:
                return BPFSchedFork(dir=results_dir, cmd_args=args)
            case _:
                bm_log(f"Unsupported bpf_program type {bpf_program_type}", LogType.FATAL)
                sys.exit(1)
