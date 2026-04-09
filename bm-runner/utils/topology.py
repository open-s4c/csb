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


class Filter:
    group_name: str  # "Node"
    idx: int  # 0

    def __init__(self, name, idx):
        self.group_name = name
        self.idx = idx


class Topology:
    # These strings are tightly coupled with
    # what lscpu understands.
    CPU = "CPU"
    CORE = "Core"
    NUMA = "Node"
    PACKAGE = "Socket"

    data_frame: pd.DataFrame

    def __init__(self):
        lscpu_out = self.__read_lscpu_info()
        self.data_frame = self.__to_data_frame(lscpu_out)

    def __read_lscpu_info(self) -> list[str]:
        """
        Runs `lscpu` and returns its output as array of lines.
        """
        # CACHE will be output as columns: L1d, L1i, L2, L3
        # this depends on the machine. Right now we don't
        # make use of CACHE and CLUSTER (usually empty column)
        # We request them in case they are needed in the future.
        cpu_info = shell_out(
            f"lscpu -p={self.CPU},{self.CORE},CACHE,{self.NUMA},{self.PACKAGE},CLUSTER",
            output_is_log=False,
            print_output=False,
            print_file_shell_cmd=False,
        )
        lines = cpu_info.strip().split("\n")
        return lines

    def __to_data_frame(self, lines: list[str]) -> pd.DataFrame:
        try:
            # Extract column header line from the out put
            # this is usually at line `3`
            header_line = lines[3].strip().lstrip("#").strip()  # Header is at line 4 (index 3)
            # Detect columns from header line, split by comma
            columns = pd.Index([col.strip() for col in header_line.split(",")])
            # Remove comment lines, data lines start at 4.
            data_lines = [line.strip() for line in lines[4:]]
            # Now, create the DataFrame directly from the data
            df = pd.DataFrame([line.split(",") for line in data_lines], columns=columns)
            # Opt-in to the new behavior
            pd.set_option("future.no_silent_downcasting", True)
            # replace empty strings to nan
            df.replace("", np.nan, inplace=True)
            # Convert columns to numeric (int), ignoring NaN values
            df = df.apply(pd.to_numeric, errors="coerce", downcast="integer")
            return df
        except Exception as e:
            bm_log(f"Could not translate given lines to a dataframe. {e}", LogType.FATAL)
            sys.exit(1)

    def __select_by_policy(
        self,
        count: int,
        filter: Optional[Filter] = None,
        one_cpu_per_core: bool = False,
        order: CpuOrder = CpuOrder.ASC,
    ):
        df = self.data_frame
        try:
            # If filter is given, we only select rows that
            # are associated by the given group
            # e.g. where df['node'] == 0
            if filter is not None:
                df = df[df[filter.group_name] == filter.idx]

            # If one CPU per core is requested,
            # we only keep rows where core index is unique.
            # This way we don't select CPUs associated
            # with the same core, preventing hyper-threading.
            if one_cpu_per_core:
                df = df.drop_duplicates(subset=[self.CORE])

            # from the filtered data frame, we take
            # the CPU column and convert it to a list.
            selected_cpus = df[self.CPU].tolist()

            # reverse the list if descending order is desired
            if order == CpuOrder.DESC:
                selected_cpus = list(reversed(selected_cpus))

            # from the selected CPUs choose the given `count`
            return self.__choose(selected_cpus, count=count)
        except Exception as e:
            bm_log(f"Could not select by policy. Due to: {e}", LogType.FATAL)
            sys.exit(1)

    def __choose(self, selected: list[int], count: int) -> list[int]:
        """
        Chooses `count` number of CPUs from the given `selected` list.
        """
        if len(selected) < count:
            bm_log(
                f"""Number of selected CPUs {len(selected)} is less than requested {count}.
                Same CPUs can be assigned to different units causing oversubscription.
            """,
                LogType.WARNING,
            )
        return list(itertools.islice(itertools.cycle(selected), count))

    def __user_choice(self, pre_selected: list[int], count: int):
        # get the max index value of preselected CPUs
        max_cpu_idx = max(pre_selected)
        # get available CPU count
        cpu_count = self.get_cpu_count()

        # confirm selected CPUs are available on the system
        # if max_cpu_idx is within range, then all of them are.
        if max_cpu_idx >= cpu_count:
            bm_log(
                f"""
                    User wants to assign to none existing CPU(s) e.g. {max_cpu_idx}.
                    Falling back to available CPUs using % CPU count.
                """,
                LogType.ERROR,
            )
            # map preselected to modular
            pre_selected = [element % cpu_count for element in pre_selected]

        return self.__choose(pre_selected, count=count)

    def select(
        self, count: int, policy: CoreAssignPolicy, pre_selected: Optional[list[int]] = None
    ) -> list[int]:
        """
        Returns a list of selected CPUs. The list length is equal to the given requested `count`.
        The CPUs are selected based on the following:

        - if `pre_selected` parameter is not None, the given preselected CPUs are used,
          provided that these CPUs are available on the system. If not, given CPU indexes
          are transformed to available CPUs using modular CPU count.
        - if `pre_selected` parameter is None, the given `policy` parameter determines
          how the CPUs are selected.

        Note that when the selected set of CPUs has less CPUs than requested in `count`, the
        CPUs are repeated. e.g. if selected CPUs are [1,2] and requested `count` is `4`,
        [1, 2, 1, 2] is returned.

        Parameters
        -------
        count: int
            requested number of CPUs.
        policy: CoreAssignPolicy
            determines the policy of what and how CPUs are selects.
            This parameter is obsolete when `pre_selected` is not None.
        pre_selected: Optional[list[int]]
            optional parameter. A list of CPU indexes to choose from.
            when pre_selected is not None, `policy` parameter becomes obsolete.
        """
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

        cpus = self.__select_by_policy(
            count=count,
            filter=filter,
            one_cpu_per_core=policy.one_cpu_per_core,
            order=policy.cpu_order,
        )
        return cpus

    def get_numas(self) -> list[int]:
        """
        Returns a list of available NUMA/node indexes.
        """
        return self.data_frame[self.NUMA].unique().tolist()

    def get_numa_count(self) -> int:
        """
        Returns detected number of NUMAs/nodes.
        """
        return len(self.get_numas())

    def get_packages(self) -> list[int]:
        """
        Returns a list of available package/socket indexes.
        """
        return self.data_frame[self.PACKAGE].unique().tolist()

    def get_package_count(self) -> int:
        """
        Returns detected number of packages.
        """
        return len(self.get_packages())

    def get_cores(self) -> list[int]:
        """
        Returns a list of available core indexes.
        """
        return self.data_frame[self.CORE].unique().tolist()

    def get_core_count(self) -> int:
        """
        Returns detected number of cores.
        """
        return len(self.get_cores())

    def get_cpus(self) -> list[int]:
        """
        Returns a list of available CPU indexes.
        """
        return self.data_frame[self.CPU].unique().tolist()

    def get_cpu_count(self) -> int:
        """
        Returns detected number of CPUs.
        """
        return len(self.get_cpus())
