# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from utils.logger import bm_log, LogType
from config.policy import CoreAssignPolicy, PackGroup, CpuOrder
from benchkit.shell.shell import shell_out
import pandas as pd
import itertools
import numpy as np
from typing import Optional
import sys
import os

class TopologyCounts:
    num_numas: int
    num_cpus: int
    num_cores: int
    num_packages: int

class Filter:
    group_name: str  # "Node"
    idx: int  # 0
    def __init__(self, name, idx):
        self.group_name = name
        self.idx = idx

class Topology:
    CPU = "CPU"
    CORE = "Core"
    L1_DATA_CACHE = "L1d"
    L1_INS_CACHE = "L1i"
    L2_CACHE = "L2"
    L3_CACHE = "L3"
    NUMA = "Node"
    PACKAGE = "Socket"
    CLUSTER = "Cluster"  # careful mostly empty

    def __init__(self):
        lines = self.__read_info()
        self.data = self.__transform_info(lines)

    def get_counts(self) -> TopologyCounts:
        stats = TopologyCounts()
        stats.num_cpus = self.data[self.CPU].unique().size
        stats.num_cores = self.data[self.CORE].unique().size
        stats.num_numas = self.data[self.NUMA].unique().size
        stats.num_packages = self.data[self.PACKAGE].unique().size
        bm_log(f"#CPUS: {stats.num_cpus }")
        bm_log(f"#CORES: {stats.num_cores}")
        bm_log(f"#NUMAS: {stats.num_numas}")
        bm_log(f"#PACKAGES: {stats.num_packages}")
        return stats

    def __transform_info(self, lines: list[str]) -> pd.DataFrame:
        # Extract column header line
        header_line = lines[3].strip().lstrip("#").strip()  # Header is at line 4 (index 3)
        columns = pd.Index([col.strip() for col in header_line.split(",")])
        # Remove comment lines
        data_lines = [line.strip() for line in lines[4:]]
        # Now, create the DataFrame directly from the data
        df = pd.DataFrame([line.split(",") for line in data_lines], columns=columns)
        # Opt-in to the new behavior
        pd.set_option("future.no_silent_downcasting", True)
        df.replace("", np.nan, inplace=True)
        # Step 2: Convert columns to numeric (int), ignoring NaN values
        df = df.apply(pd.to_numeric, errors="coerce", downcast="integer")
        return df

    def __read_info(self) -> list[str]:
        cpu_info = shell_out(
            "lscpu -p=CPU,CORE,CACHE,NODE,SOCKET,CLUSTER",
            output_is_log=False,
            print_output=False,
            print_file_shell_cmd=False,
        )
        lines = cpu_info.strip().split("\n")
        return lines

    def __pack_by(
        self,
        count: int,
        filter: Optional[Filter] = None,
        one_per_core: bool = False,
        desc: bool = True,
        distance: int = 0,
    ):
        df = self.data

        if filter is not None:
            df = df[df[filter.group_name] == filter.idx]

        if one_per_core:
            num_cores = len(df[self.CORE].unique())
            df = df.drop_duplicates(subset=[self.CORE])
            assert num_cores == len(df)

        selected_group = df[self.CPU].tolist()
        if desc:
            selected_group = list(reversed(selected_group))

        return list(itertools.islice(itertools.cycle(selected_group), count))

    def __user_choice(self, pre_selected: list[int], count: int):
        max_cpu = max(pre_selected)
        cpu_count = max(self.data[self.CPU]) + 1

        assert cpu_count == os.cpu_count()

        if max_cpu >= cpu_count:
            bm_log(
                f"User want to assign to none existing CPU(s) {max_cpu}. Falling back to available CPUs",
                LogType.ERROR,
            )
            pre_selected = [element % cpu_count for element in pre_selected]

        cpus = list(itertools.islice(itertools.cycle(pre_selected), count))
        assert len(cpus) == count, "[BUG] returning shorter list than requested"
        return cpus

    def select(
        self, count: int, policy: CoreAssignPolicy, pre_selected: Optional[list[int]] = None
    ) -> list[int]:
        if pre_selected is not None:
            return self.__user_choice(pre_selected, count)

        filter: Optional[Filter] = None
        match policy.pack_group:
            case PackGroup.PACKAGE:
                filter = Filter(self.PACKAGE, 0)
            case PackGroup.NUMA:
                filter = Filter(self.NUMA, 0)
            case PackGroup.NO_PACK:
                filter = None
            case _:
                bm_log(f"Case: {policy.pack_group} not handled!", LogType.ERROR)
                sys.exit(1)
        desc = True if policy.cpu_order == CpuOrder.DESC else False
        cpus = self.__pack_by(
            count=count, filter=filter, one_per_core=policy.one_cpu_per_core, desc=desc
        )
        return cpus
