# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import subprocess
import signal
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
from monitors.monitor import Monitor
from bm_utils import ensure_exists
from utils.logger import bm_log
from typing import Optional


class SarCmd:
    def __init__(self, output_dir: str, cmd_args: list[str] = []):
        cmds = ["sudo", "ip", "netns", "exec"]
        cmds.append(cmd_args[0])
        cmds.extend(["sar", "-n", "DEV,EDEV", "-o", "netstats.sar"])
        cmds.extend(["--iface={}".format(cmd_args[1]), "1"])
        cmd_str = " ".join(cmds)
        bm_log(f"Running sar: {cmd_str}")
        self.process = subprocess.Popen(
            cmds,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp,
            cwd=output_dir,
        )

    def stop(self):
        # This acts like ctrl+C
        self.process.send_signal(signal.SIGINT)
        self.process.wait()


class SarNetStats(Monitor):
    def __init__(self, output_dir: str, args: list[str] = []):
        for tool in ["sar", "sadf"]:
            ensure_exists(tool)
        super().__init__(dir=output_dir, args=args)
        self.sar: Optional[SarCmd] = None

    def start(self):
        # Launch perf in the background
        self.sar = SarCmd(self.dir, self.args)

    def collect_results(self):
        proc = subprocess.run(
            [
                "sadf",
                "-dh",
                "netstats.sar",
                "--",
                "-n",
                "DEV,EDEV",
                "--iface={}".format(self.args[1]),
            ],
            capture_output=True,
            cwd=self.dir,
        )
        data = pd.read_csv(StringIO(proc.stdout.decode("utf-8")), sep=";")

        agg_data = data.agg(
            {
                "rxpck/s": "mean",
                "txpck/s": "mean",
                "rxkB/s": "mean",
                "txkB/s": "mean",
                "rxcmp/s": "mean",
                "txcmp/s": "mean",
                "rxmcst/s": "mean",
                "%ifutil[...]": "mean",
                "rxerr/s": "mean",
                "txerr/s": "mean",
                "rxdrop/s": "mean",
                "txdrop/s": "mean",
                "coll/s": "mean",
                "txcarr/s": "mean",
                "rxfram/s": "mean",
                "rxfifo/s": "mean",
                "txfifo/s[...]": "mean",
            }
        )
        return "".join(["{}={};".format(i, v) for i, v in agg_data.items()])

    def plot(self):
        proc = subprocess.run(
            [
                "sadf",
                "-dh",
                "netstats.sar",
                "--",
                "-n",
                "DEV,EDEV",
                "--iface={}".format(self.args[1]),
            ],
            capture_output=True,
            cwd=self.dir,
        )
        data = pd.read_csv(StringIO(proc.stdout.decode("utf-8")), sep=";")
        data["time"] = pd.to_datetime(data["timestamp"])
        data["time"] = (data["time"] - data["time"].iloc[0]).dt.total_seconds()

        plotsets = [
            ("Packets per second", "pcks", ["rxpck/s", "txpck/s"]),
            ("kB per second", "kbs", ["rxkB/s", "txkB/s"]),
            ("NIC utilization percentage", "util", ["%ifutil[...]"]),
            (
                "Errors",
                "errors",
                [
                    "rxerr/s",
                    "txerr/s",
                    "rxdrop/s",
                    "txdrop/s",
                    "coll/s",
                    "txcarr/s",
                    "rxfram/s",
                    "rxfifo/s",
                    "txfifo/s[...]",
                ],
            ),
        ]
        for title, fname, ylist in plotsets:
            data.plot("time", y=ylist)
            plt.title("{} {}".format(title, self.args[1]))
            plt.xlabel("Seconds Elapsed")
            plt.legend(
                loc="upper left",
                bbox_to_anchor=(1, 1),
                borderaxespad=0.3,
                fontsize=4.5,
            )
            filename = os.path.join(self.dir, f"{fname}.png")
            plt.savefig(filename)
            plt.close()

    def stop(self):
        if self.sar is not None:
            self.sar.stop()
            self.plot()
