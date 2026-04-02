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
        return stats

    def __transform_info(self, lines: list[str]) -> pd.DataFrame:
        # Extract column header line
        header_line = lines[3].strip().lstrip("#").strip()  # Header is at line 4 (index 3)
        columns = [col.strip() for col in header_line.split(",")]
        # Remove comment lines
        data_lines = [line.strip() for line in lines[4:]]
        # Now, create the DataFrame directly from the data
        df = pd.DataFrame([line.split(',') for line in data_lines], columns=columns)
        return df

    def __read_info(self) -> list[str]:
        cpu_info = shell_out("lscpu -p=CPU,CORE,CACHE,NODE,SOCKET,CLUSTER",
                              output_is_log=False,
                              print_output=False,
                              print_file_shell_cmd=False)
        lines = cpu_info.strip().split("\n")
        return lines

    def __pack_by(self, count:int, groub:str, one_per_core: bool = False):
        df = self.__one_per_core() if one_per_core else self.data
        groups = df.groupby(groub)[self.CPU].apply(list).to_dict()
        selected_group = max(groups.values(), key=len)
        return list(itertools.islice(itertools.cycle(selected_group), count))

    def __one_per_core(self):
        return self.data.groupby(self.CORE).first().reset_index()

    def pack_by_numa(self, count:int, one_per_core: bool):
        return self.__pack_by(count, self.NUMA, one_per_core)

    def pack_by_pkg(self, count:int, one_per_core: bool):
        return self.__pack_by(count, self.PACKAGE, one_per_core)


