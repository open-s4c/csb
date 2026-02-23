# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import sys
import bm_utils
import subprocess
from bm_executer import Executer
from bm_executer import ExecutionUnit
from bm_utils import stop_process
from bm_config import Application
from config.benchmark import ExecutionType
from utils.logger import bm_log, LogType
from bm_utils import resolve_path


class Process(ExecutionUnit):
    def __init__(self, idx, home_dir, record_data_dir, core_set, app: Application):
        super().__init__(idx=idx, home_dir=home_dir, app=app, type=ExecutionType.NATIVE)
        self.record_data_dir = record_data_dir
        self.core_set = core_set

    def get_results_dir(self) -> str:
        return str(resolve_path(self.record_data_dir, use_in_container=False))

    def exec(self, command):
        change_dir = ""
        if self.app.cd:
            assert self.app.path is not None, "path is not set while change directory is requested!"
            change_dir = f" cd {self.app.path} && "
        commands = (
            f"{self.CMD_WHILE_NOT_START}{change_dir}taskset --cpu-list {self.core_set} {command}"
        )
        with open(resolve_path(self.output_file), "w") as outfile:
            self.process = subprocess.Popen(
                commands,
                shell=True,
                stdout=outfile,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp,
                cwd=self.home_dir,
            )
        bm_log(f"launched process {self.name} with {commands}")

    def wait(self):
        self.process.wait()
        if self.process.returncode != 0:
            bm_log(
                f"process {self.name} has failed/or crashed with return code {self.process.returncode}",
                LogType.FATAL,
            )
            sys.exit(1)

    def stop(self):
        if self.process is not None:
            stop_process(self.process.pid)


class Processes(Executer):
    def __init__(
        self,
        home_dir,
        count,
        record_data_dir,
        cpus_per_proc,
        core_affinity_offset_list,
        apps: list[Application],
    ):
        super().__init__(home_dir=home_dir, results_dir=record_data_dir)
        assert len(apps) == count, "[BUG] Application list length must be equal to count"
        for i in range(count):
            core_set = bm_utils.get_cpu_set(
                start=core_affinity_offset_list[i], core_cnt=cpus_per_proc
            )
            proc = Process(
                idx=i,
                home_dir=home_dir,
                core_set=core_set,
                record_data_dir=record_data_dir,
                app=apps[i],
            )
            self.add_exec_unit(proc)
