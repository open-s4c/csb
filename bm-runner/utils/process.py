# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import signal
import subprocess
from utils.logger import bm_log, LogType
from typing import Optional
from bm_utils import ensure_exists


class BackgroundProcess:
    TIMEOUT_SEC = 5
    Env = {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}

    def __init__(
        self,
        name: str,
        out_dir: str,
        cmds: list[str],
        wdir: Optional[str] = None,
        ofile_name: Optional[str] = None,
        requires: list[str] = [],
    ):
        assert len(cmds) > 1, "expected at least the process name"
        self.name = name
        self.efile_name = os.path.join(out_dir, f"{self.name}.err")
        if ofile_name is None:
            self.ofile_name = os.path.join(out_dir, f"{self.name}.log")
        else:
            self.ofile_name = os.path.join(out_dir, ofile_name)
        self.cmds = cmds
        self.wdir = out_dir if wdir is None else wdir
        self.process: Optional[subprocess.Popen] = None
        self.ofile = None
        self.efile = None
        # ensure process exist
        for tool in requires:
            ensure_exists(tool)

    def start(self):
        assert self.process is None, "it seems, it has already been started!"
        self.ofile = open(self.ofile_name, "w")
        self.efile = open(self.efile_name, "w")
        self.process = subprocess.Popen(
            self.cmds,
            stdout=self.ofile,
            stderr=self.efile,
            env=self.Env,
            preexec_fn=os.setpgrp,
            cwd=self.wdir,
        )
        cmd_str = " ".join(self.cmds)
        bm_log(f"[{self.name}] started: {cmd_str}")

    def __close_file(self, file):
        try:
            if file:
                file.close()
        except Exception as e:
            bm_log(f"Failed to close file {e}", LogType.ERROR)

    def __terminate(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
            bm_log(f" {self.name} terminated with {self.process.returncode}")

    def stop(self):
        if self.process is None:
            return
        bm_log(f"[{self.name}] stopping")
        self.process.send_signal(signal.SIGINT)
        try:
            self.process.wait(self.TIMEOUT_SEC)
            bm_log(f"[{self.name}] stopped with return code {self.process.returncode}")
        except subprocess.TimeoutExpired:
            bm_log(f"{self.name} timeout on exit!", LogType.ERROR)
            self.__terminate()
        finally:
            self.__terminate()
            self.__close_file(self.ofile)
            self.__close_file(self.efile)

    def read_output(self):
        try:
            with open(self.ofile_name, "r") as file:
                return file.read()
        except Exception as e:
            bm_log(f"Failed to read {self.ofile_name} {e}", LogType.ERROR)
            return ""
