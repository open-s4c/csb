# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import sys
import subprocess
from monitors.monitor import Monitor
from utils.logger import bm_log, LogType
from utils.process import BackgroundProcess


class FlameGraph(Monitor):
    FG_PATH_ENV_VAR_NAME = "FLAMEGRAPH"

    def __init__(self, output_dir: str, args: list[str] = ["-a"]):
        super().__init__(dir=output_dir, args=args)
        cmds = ["sudo", "perf", "record", "-F", "99", "-g"]
        cmds.extend(args)
        self.perf = BackgroundProcess(
            name="perf", out_dir=output_dir, cmds=cmds, requires=["perf"], pin=self.get_cpus()
        )
        self.fg_path = os.getenv(self.FG_PATH_ENV_VAR_NAME)
        if self.fg_path is None:
            bm_log(
                f"{self.FG_PATH_ENV_VAR_NAME} environment variable is not set. Set it to the path of `stackcollapse-perf.pl` and try again. Or remove perf from monitors",
                LogType.FATAL,
            )
            sys.exit(1)

    def start(self):
        # Launch perf in the background
        self.perf.start()

    def collect_results(self, pids: Optional[list[int]]):
        return ""

    def __generate_flamegraph(self, errfile):
        """
        Generates flamegraph on perf.data in output dir
        """
        # run perf script on the perf.data in results folder
        perf = subprocess.Popen(
            ["sudo", "perf", "script", "-i", "perf.data"],
            cwd=self.dir,
            stdout=subprocess.PIPE,
            stderr=errfile,
        )
        # run stack collapse on the output of perf record
        stacks_file = os.path.join(self.dir, "flamegraph.stacks")
        with open(stacks_file, "w") as stacks:
            try:
                subprocess.run(
                    [f"{self.fg_path}/stackcollapse-perf.pl"],
                    stdin=perf.stdout,
                    stdout=stacks,
                    stderr=errfile,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                bm_log(f"Failed to generate flamegraph: {e}", LogType.ERROR)
            finally:
                if perf.stdout:
                    perf.stdout.close()
        svg = os.path.join(self.dir, "flamegraph.svg")
        # run flamegraph on the output of stackcollapse
        # and save the output in svg
        with open(svg, "w") as svg, open(stacks_file, "r") as stacks:
            try:
                subprocess.run(
                    [f"{self.fg_path}/flamegraph.pl"],
                    stdin=stacks,
                    stdout=svg,
                    stderr=errfile,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                bm_log(f"Failed to generate flamegraph: {e}", LogType.ERROR)

    def stop(self):
        if self.perf is not None:
            self.perf.stop()
            with open(os.path.join(self.dir, "flamegraph.errors"), "w") as errfile:
                self.__generate_flamegraph(errfile)
