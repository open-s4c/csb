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
from utils.process import BackgroundProcess

class SarNetStats(Monitor):
    def __init__(self, output_dir: str, args: list[str] = []):
        super().__init__(dir=output_dir, args=args)
        for tool in ["sar", "sadf"]:
            ensure_exists(tool)
        cmds = ["sudo", "ip", "netns", "exec"]
        cmds.append(args[0])
        cmds.extend(["sar", "-n", "DEV,EDEV", "-o", "netstats.sar"])
        cmds.extend(["--iface={}".format(args[1]), "1"])
        self.sar = BackgroundProcess(name="SarNetStats", out_dir=output_dir, cmds=cmds, check_exists=False)

    def start(self):
        self.sar.start()

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
        self.sar.stop()
        self.plot()
