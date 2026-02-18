# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import sys
import shutil
from typing import Optional
from config.adapter import Adapter
from bm_utils import exists_system_wide
from pathlib import Path
from bm_utils import ensure_exists
from utils.logger import bm_log, LogType


class Application(dict):
    CONFIG_KEY: str = "applications"
    DISTRIBUTION_SUM = 1024
    BUILTIN_APP_DIR = "build/bench"

    def __init__(
        self,
        name: str,
        operations: list[int] = [],
        path: Optional[Path] = None,
        args: Optional[str] = None,
        adapter: Optional[Adapter] = None,
    ):
        """
        An application is either a builtin benchmark binary from the `bench` directory,
        or an external application/benchmark binary.
        This configuration defines an array of applications, each with their own setup.
        If this array has more than one application.
        each container will run an application from the array in a round robin fashion.
        Represented as a JSON array of objects.

        Parameters
        ----------
        name: str
            The name of the application/benchmark binary.
        path: Optional[Path]
            The dir where the application/benchmark binary exists. Required if it does not exist
            system wide.
        operations: list[int]
            A list of integers representing the distribution of operations.
            The sum of all values in the list must be equal to 1024.
            Each index represents a specific operation as defined by the benchmark/application.
            This is only relevant for builtin benchmarks.
        args: Optional[str] = -t={threads} -n={noise} -d={duration} -s={initial_size}
            A string that represents the command line arguments of the application.
            It can contain place holders for dynamic values. Available place holders:
            are `{threads}`, `{noise}`, `{duration}`, `{index}`, and `{initial_size}`.
            They are replaced at runtime with the actual values: number of threads, number of nop instructions following an operation,
            duration of the benchmark in seconds, the index of the execution unit in the current benchmarking run, and initial size of the data structure respectively.
            If any of the above is relevant for the external application they can be used in the args
            string. Otherwise they can be omitted.
        adapter: Optional[Adapter] = {}
            An adapter object.
            This is only relevant for external applications/benchmarks.
        -
        """
        super().__init__(
            name=name, path=path, op_distributions=operations, args=args, adapter=adapter
        )
        self.name = name
        self.path = path
        self.operations = operations
        # Set default framework arguments
        self.args = (
            "-t={threads} -n={noise} -d={duration} -s={initial_size}" if args is None else args
        )
        self.adapter = Adapter(**adapter) if adapter is not None else None
        if len(self.operations) > 0 and sum(self.operations) != self.DISTRIBUTION_SUM:
            bm_log(
                f"The operations distribution sum must be equal to {self.DISTRIBUTION_SUM}",
                LogType.FATAL,
            )
            sys.exit(1)

    def __get_runnable_cmd(self, work_dir: Path) -> str:
        binary_path = os.path.join(work_dir, self.BUILTIN_APP_DIR)
        if self.path:
            fname = ensure_exists(name=self.name, dir=self.path)
            shutil.copy(fname, os.path.join(binary_path, self.name))
        else:
            if exists_system_wide(self.name):
                return f"{self.name} "
            fname = ensure_exists(name=self.name, dir=binary_path)
        return f"./{os.path.join(self.BUILTIN_APP_DIR, self.name)} "

    def get_cmd(self, threads, duration, noise, initial_size, index, work_dir: Path) -> str:
        cmd = self.__get_runnable_cmd(work_dir)
        cmd += " ".join(f"-op{idx}={val} " for idx, val in enumerate(self.operations))
        cmd += self.args.format(
            threads=threads,
            duration=duration,
            noise=noise,
            initial_size=initial_size,
            index=index,
        )
        bm_log(f"generated command: {cmd}")
        return cmd
