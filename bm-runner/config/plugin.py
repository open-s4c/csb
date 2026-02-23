# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from enum import Enum
import os
import tempfile
import subprocess
import sys
from bm_utils import stop_process
from typing import Optional
from utils.logger import bm_log, LogType
from bm_utils import ensure_exists
from pathlib import Path


class ExecutionTime(str, Enum):
    """
    Execution time of the plugin script/process.

    Members
    ----------
    PRE: The script/process will be launched before the start signal.
    POST: The script/process will be launched after the start signal.
    CLEANUP: The script/process will be called after the benchmark is finished or interrupted.
    WITH: The script/process will be called at the same time as the benchmark as a wrapper.
    """

    PRE = "pre"
    POST = "post"
    CLEANUP = "cleanup"
    WITH = "with"


# Example of a valid Json
# "plugins" : [ { path: "<valid path>", name: "<script_name>", exec_time = "pre", args = ["1", "2"]}]
# note that `args` has to be a list of strings
class Plugin(dict):
    ENV_VAR = "CSB_PLUGINS"
    CONFIG_KEY: str = "plugins"

    def __init__(
        self,
        name: str,
        exec_time: ExecutionTime,
        path: Optional[Path] = None,
        args: list[str] = [],
        force_stop: bool = False,
    ):
        """
        Plugins are a flexible way to inject additional scripts/processes to be executed
        at different stages of the benchmark execution.
        A good example would be to start a client to communicate with a server benchmark
        before the server starts accepting connections.
        Represented as a JSON array of objects.
        Parameters
        ----------
        name: str
            Name of the script/process to be executed.
        exec_time: ExecutionTime
            When to execute the script/process (pre, post, cleanup).
        path: Optional[str]
            Path to the script/process. It will look under scripts/plugins
            or if it is available system wide.
        args: list[str]
            List of arguments to be passed to the script/process.
            It can include one place holder: `{homedir}`.
            This is replaced at runtime with the path of the build directory of the CSB project.
        force_stop: bool
            Whether to forcefully stop the process if it is still running during cleanup.
        -
        """
        super().__init__(name=name, path=path, args=args)
        self.name = name
        self.path = path
        self.args = args
        self.exec_time = exec_time
        self.force_stop = force_stop
        self.process = None
        self.fname = ensure_exists(name, dir=path, env_var_dir=self.ENV_VAR)

    def get_command(self) -> str:
        commands = [self.fname]
        commands.extend(self.args)

        return " ".join(commands)

    def execute(self, results_dir, **kwargs):
        tmpfile = tempfile.NamedTemporaryFile(dir=results_dir, delete=False)
        commands = [self.fname]
        if self.args is not None:
            commands.extend(map(lambda arg: arg.format(**kwargs), self.args))

        self.process = subprocess.Popen(
            commands, stdout=tmpfile, stderr=tmpfile, preexec_fn=os.setpgrp
        )
        if self.process.poll() is None:
            bm_log(f"Launched {' '.join(commands)} -> Output file: {tmpfile.name}")
        else:
            bm_log(
                f"Could not launch {self.name}, got return code {self.process.returncode}",
                LogType.FATAL,
            )
            sys.exit(1)

    def stop(self):
        if self.process is not None:
            if self.force_stop:
                bm_log(f"Killing {self.name}, with PID = {self.process.pid}")
                stop_process(self.process.pid)
            else:
                bm_log(f"Waiting for {self.name}, with PID = {self.process.pid} to terminate")
                self.process.wait()
