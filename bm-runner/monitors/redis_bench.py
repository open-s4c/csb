# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import pandas as pd
from pathlib import Path
from monitors.monitor import Monitor
from typing import Optional


class RedisStats(Monitor):
    def __init__(self, output_dir: Path, args: list[str] = []):
        super().__init__(dir=output_dir, args=args)
        assert len(args) > 0, "at least one argument should be there"
        self.fname = args[0]

    def start(self):
        pass

    def stop(self):
        pass

    def collect_results(self, pids: Optional[list[int]]) -> str:
        data = pd.read_csv(self.dir / self.fname)
        # OK/NOT OK: redis-benchmark provides the statistics like requests per seconds, avg. latency, etc. as a list for a number of requests. What we want to achieve here is to aggregate the lists per metric into a single number. It should be statistically meaningful to calculate average RPS and latency with mean, and min and max latencies with the corresponding functions (OK), but it is probably not right for p50/p95/p99 latencies (NOT OK).
        agg_data = data.agg(
            {
                "rps": "mean",  # OK
                "avg_latency_ms": "mean",  # OK
                "min_latency_ms": "min",  # OK
                "p50_latency_ms": "mean",  # NOT OK?
                "p95_latency_ms": "max",  # NOT OK
                "p99_latency_ms": "max",  # NOT OK
                "max_latency_ms": "max",  # OK
            }
        )
        return "".join(["{}={};".format(i, v) for i, v in agg_data.items()])
