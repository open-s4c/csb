import sys
from enum import Enum

from utils.logger import bm_log, LogType
from config.env_config import EnvUniversalConfig, UniversalConfig

from monitors.bpftrace_programs.bpf_program import BPFProgram
from monitors.bpftrace_programs.bpf_block_req import BPFBlockReq
from monitors.bpftrace_programs.bpf_sched_latency import BPFSchedLatency
from monitors.bpftrace_programs.bpf_sched_migrate_task import BPFSchedMigrateTask
from monitors.bpftrace_programs.bpf_sched_fork import BPFSchedFork
from monitors.bpftrace_programs.bpf_sched_domains_mutex import BPFSchedDomainsMutex
from monitors.bpftrace_programs.bpf_vfs_read_latency import BPFVfsReadLatency
from monitors.bpftrace_programs.bpf_cgroup_rstat_lock_cont import BPFCGroupRstatLockCont

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
    block_req = "block_req"
    sched_latency = "sched_latency"
    sched_migrate_task = "sched_migrate_task"
    sched_fork = "sched_fork"
    sched_domains_mutex = "sched_domains_mutex"
    vfs_read_latency = "vfs_read_latency"
    cgroup_rstat_lock_cont = "cgroup_rstat_lock_cont"

class BPFProgramFactory:
    @staticmethod
    def create(bpf_program_type: BPFProgramType, results_dir, args) -> BPFProgram:
        # if the user has requested to disable the monitors,
        # we return a dummy monitor that does nothing,
        # so that the rest of the code can remain unchanged
        name={bpf_program_type}
        if not EnvUniversalConfig.is_on(UniversalConfig.CSB_ANALYZE):
            return DummyBPFProgram(name)  # Return a dummy bpf_program that does nothing
        match bpf_program_type:
            case BPFProgramType.block_req:
                return BPFBlockReq(name, dir=results_dir, args=args)
            case BPFProgramType.cgroup_rstat_lock_cont:
                return BPFCGroupRstatLockCont(name, dir=results_dir, args=args)
            case BPFProgramType.sched_latency:
                return BPFSchedLatency(name, dir=results_dir, args=args)
            case BPFProgramType.sched_migrate_task:
                return BPFSchedMigrateTask(name, dir=results_dir, args=args)
            case BPFProgramType.sched_fork:
                return BPFSchedFork(name, dir=results_dir, args=args)
            case BPFProgramType.sched_domains_mutex:
                return BPFSchedDomainsMutex(name, dir=results_dir, args=args)
            case BPFProgramType.vfs_read_latency:
                return BPFVfsReadLatency(name, dir=results_dir, args=args)
            case _:
                bm_log(f"Unsupported bpf_program type {name}", LogType.FATAL)
                sys.exit(1)
