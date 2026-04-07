# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from enum import Enum
from utils.logger import bm_log, LogType
import glob
import os
import os
import glob
import enum
import subprocess
from config.policy import CoreAssignPolicy
from benchkit.shell.shell import shell_out
import re
import pandas as pd
import itertools
import numpy as np

class OperatingSystem(str, Enum):
    Ubuntu = "Ubuntu"
    openEuler = "openEuler"
    Unsupported = "unsupported"


def get_os() -> OperatingSystem:
    OS_INFO_FILE = "/etc/os-release"
    try:
        with open(OS_INFO_FILE) as f:
            content = f.read()
        if OperatingSystem.openEuler.value in content:
            return OperatingSystem.openEuler
        elif OperatingSystem.Ubuntu.value in content:
            return OperatingSystem.Ubuntu
        else:
            bm_log(f"Could not detect operating system in {content}!", LogType.WARNING)
            return OperatingSystem.Unsupported
    except FileNotFoundError:
        bm_log(
            f"Could not detect operating system. {OS_INFO_FILE} does not exist!", LogType.WARNING
        )
        return OperatingSystem.Unsupported

subprocess


# -----------------------------
# Helpers
# -----------------------------

def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except:
        return None


def _parse_list(s):
    if not s:
        return set()
    out = set()
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


# -----------------------------
# Topology Discovery
# -----------------------------

class TopologyCounts:
    num_numas: int
    num_cpus: int
    num_cores: int
    num_packages: int

class Topology:
    CPU = "CPU"
    CORE = "Core"
    L1_DATA_CACHE = "L1d"
    L1_INS_CACHE = "L1i"
    L2_CACHE = "L2"
    L3_CACHE = "L3"
    NUMA = "Node"
    PACKAGE = "Socket"
    CLUSTER = "Cluster" # careful mostly empty

    def __init__(self):
        lines = self.__read_info()
        self.data = self.__transform_info(lines)
        pass

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
        columns = [col.strip() for col in header_line.split(",")]
        # Remove comment lines
        data_lines = [line.strip() for line in lines[4:]]
        # Now, create the DataFrame directly from the data
        df = pd.DataFrame([line.split(',') for line in data_lines], columns=columns)
        df.replace('', np.nan, inplace=True)
        # Step 2: Convert columns to numeric (int), ignoring NaN values
        df = df.apply(pd.to_numeric, errors='coerce', downcast='integer')
        return df

    def __read_info(self) -> list[str]:
        cpu_info = shell_out("lscpu -p=CPU,CORE,CACHE,NODE,SOCKET,CLUSTER",
                              output_is_log=False,
                              print_output=False,
                              print_file_shell_cmd=False)
        cpu_info = shell_out("cat /home/lilith/workspace/csb/ampere.csv",
                             print_output=False,
                             print_file_shell_cmd=False)
        lines = cpu_info.strip().split("\n")
        return lines

    def __pack_by(self, count:int, group:str, one_per_core: bool = False, filter: int = 0):
        df = self.data
        df = df[df[group] == filter] # pick one per group
        if one_per_core:
            df = df.drop_duplicates(subset=self.CORE)
        selected_group = df[self.CPU].tolist()
        return list(itertools.islice(itertools.cycle(selected_group), count))

    def __one_per_core(self):
        return self.data.groupby(self.CORE).first().reset_index()

    def pack_by_numa(self, count:int, one_per_core: bool):
        return self.__pack_by(count, self.NUMA, one_per_core)

    def pack_by_pkg(self, count:int, one_per_core: bool):
        return self.__pack_by(count, self.PACKAGE, one_per_core)

    def cpu_distance(self, a, b):
        row_a = self.data[self.data['CPU'] == a].iloc[0]
        row_b = self.data[self.data['CPU'] == b].iloc[0]

        score = 0

        # NUMA distance
        if row_a['Node'] != row_b['Node']:
            score += 1000

        # Package distance
        if row_a['Socket'] != row_b['Socket']:
            score += 500

        # Core distance
        if row_a['Core'] != row_b['Core']:
            score += 10

        # SMT distance (same core but different thread)
        if row_a['Core'] == row_b['Core'] and a != b:
            score -= 50  # penalize SMT siblings

        return score


    def select_cpus(self, n):
        cpus = list(map(int, self.data[self.CPU].values))

        if n == 1:
            return [cpus[0]]

        # Step 1: find farthest pair
        best_pair = None
        best_score = -1
        for i, a in enumerate(cpus):
            for b in cpus[i+1:]:
                s = self.cpu_distance(a, b)
                if s > best_score:
                    best_score = s
                    best_pair = [a, b]

        selected = best_pair[:]

        # Step 2: greedy add farthest from all selected
        while len(selected) < min(n, len(cpus)):
            best_cpu = None
            best_score = -1
            for c in cpus:
                if c in selected:
                    continue
                score = sum(self.cpu_distance(c, s) for s in selected)
                if score > best_score:
                    best_score = score
                    best_cpu = c
            selected.append(best_cpu)

        # Step 3: wrap if n > #cpus
        # if len(selected) < n:
        #     wrapped = []
        #     while len(wrapped) < n:
        #         for c in selected:
        #             wrapped.append(c)
        #             if len(wrapped) == n:
        #                 break
        #     return wrapped

        return selected
