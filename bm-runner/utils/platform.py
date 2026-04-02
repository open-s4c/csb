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
        print(lines)
        self.data = self.__transform_info(lines)
        print(self.data)
        pass

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
        cpu_info = shell_out("lscpu -p=CPU,CORE,CACHE,NODE,SOCKET,CLUSTER", print_file_shell_cmd=False)
        print(cpu_info)
        lines = cpu_info.strip().split("\n")
        return lines

class CpuTopology:
    def __init__(self):
        self.topo = self._load_topology()
        self.cpus = sorted(self.topo.keys())

    def _load_topology(self):
        topo = {}
        for path in glob.glob("/sys/devices/system/cpu/cpu[0-9]*"):
            cpu = int(path.split("cpu")[-1])
            t = os.path.join(path, "topology")

            topo[cpu] = {
                "core_id": _read(os.path.join(t, "core_id")),
                "package_id": _read(os.path.join(t, "physical_package_id")),
                "thread_siblings": _parse_list(
                    _read(os.path.join(t, "thread_siblings_list"))
                ),
                "core_siblings": _parse_list(
                    _read(os.path.join(t, "core_siblings_list"))
                ),
            }
        return topo

    # -----------------------------
    # Distance metric (universal)
    # -----------------------------
    def cpu_distance(self, a, b):
        ta, tb = self.topo[a], self.topo[b]
        score = 0

        # NUMA distance
        if ta["package_id"] != tb["package_id"]:
            score += 1000

        # L3 cache group distance
        if b not in tb["core_siblings"]:
            score += 100

        # Core distance
        if ta["core_id"] != tb["core_id"]:
            score += 10

        # SMT distance
        if b not in tb["thread_siblings"]:
            score += 1

        return score

    # -----------------------------
    # Public selection API
    # -----------------------------
    def select(self, n, policy=CoreAssignPolicy.MAX_DISTANCE):
        cpus = list(self.cpus)

        # Even/odd filters
        if policy == CoreAssignPolicy.EVEN_ONLY:
            cpus = [c for c in cpus if c % 2 == 0]
        elif policy == CoreAssignPolicy.ODD_ONLY:
            cpus = [c for c in cpus if c % 2 == 1]

        if not cpus:
            return []

        if policy == CoreAssignPolicy.SPREAD_NUMA:
            base = self._spread_by_numa(cpus, min(n, len(cpus)))  # Updated for NUMA
        elif policy == CoreAssignPolicy.PACK_NUMA:
            base = self._pack_by_numa(cpus, min(n, len(cpus)))  # Updated for NUMA
        elif policy == CoreAssignPolicy.SPREAD_L3:
            base = self._spread_by_siblings(cpus, "core_siblings", min(n, len(cpus)))
        elif policy == CoreAssignPolicy.AVOID_SMT:
            base = self._avoid_smt(cpus, min(n, len(cpus)))
        else:  # MAX_DISTANCE (default)
            base = self._max_distance(cpus, min(n, len(cpus)))

        # Wrap around if caller asks for more than we have
        if len(base) < n:
            wrapped = []
            while len(wrapped) < n:
                for c in base:
                    wrapped.append(c)
                    if len(wrapped) == n:
                        break
            return wrapped

        return base

    # -----------------------------
    # Policy implementations
    # -----------------------------

    def _spread_by_numa(self, cpus, n):
        """
        Spread CPUs across NUMA nodes, ensuring maximum diversity in terms of NUMA nodes.
        """
        # Group CPUs by their NUMA node (package_id is usually tied to NUMA node in most systems)
        numa_groups = {}
        for c in cpus:
            numa_node = self.topo[c]["package_id"]  # treat package_id as NUMA node ID
            numa_groups.setdefault(numa_node, []).append(c)

        # Spread CPUs across different NUMA nodes
        out = []
        while len(out) < n:
            for numa_node, group in numa_groups.items():
                if group:
                    out.append(group.pop(0))  # Pop one CPU from the NUMA group
                if len(out) == n:
                    break

        return out

    def _pack_by_numa(self, cpus, n):
        """
        Pack CPUs into the same NUMA node, prioritizing nodes with the most available CPUs.
        """
        # Group CPUs by NUMA node
        numa_groups = {}
        for c in cpus:
            numa_node = self.topo[c]["package_id"]
            numa_groups.setdefault(numa_node, []).append(c)

        # Find the largest NUMA group
        largest_numa_group = max(numa_groups.values(), key=len)

        # Return the first `n` CPUs from the largest NUMA group
        return largest_numa_group[:n]

    def _spread_by_siblings(self, cpus, sib_key, n):
        used_groups = set()
        out = []
        for c in cpus:
            group = tuple(sorted(self.topo[c][sib_key]))
            if group not in used_groups:
                used_groups.add(group)
                out.append(c)
                if len(out) == n:
                    break
        return out

    def _avoid_smt(self, cpus, n):
        used = set()
        out = []
        for c in cpus:
            if any(s in used for s in self.topo[c]["thread_siblings"]):
                continue
            out.append(c)
            used.update(self.topo[c]["thread_siblings"])
            if len(out) == n:
                break
        return out

    # -----------------------------
    # MAX_DISTANCE helpers
    # -----------------------------

    def _max_distance_pair(self, cpus):
        # brute-force farthest pair
        best = (cpus[0], cpus[1])
        best_score = -1
        for i, a in enumerate(cpus):
            for b in cpus[i + 1:]:
                s = self.cpu_distance(a, b)
                if s > best_score:
                    best_score = s
                    best = (a, b)
        return list(best)

    def _max_distance(self, cpus, n):
        if n == 1:
            return [cpus[0]]

        # detect flat topology (all distances equal)
        scores = set()
        for i, a in enumerate(cpus):
            for b in cpus[i + 1:]:
                scores.add(self.cpu_distance(a, b))
                if len(scores) > 1:
                    break
            if len(scores) > 1:
                break

        if len(scores) <= 1:
            # fallback: evenly spaced
            step = max(1, len(cpus) // n)
            return [cpus[i] for i in range(0, len(cpus), step)][:n]

        if n == 2:
            return self._max_distance_pair(cpus)

        selected = self._max_distance_pair(cpus)
        while len(selected) < n:
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
        return selected
