# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os

from typing import Optional
from typing import Union
from utils.logger import bm_log, LogType


class RangeConfig(dict):
    def __init__(self, min: int, max: int, step: int):
        """
        Parameters
        ----------
        min: int
            start value
            JSON example: `"min": 1`
        max: int
            end value
            JSON example: `"max": 5`
        step: int
            increment step
            JSON example: `"step": 2`
            with min = 1, and max = 5, this becomes a list = `[1, 3, 5]`
        -
        """
        super().__init__(min=min, max=max, step=step)
        self.min = min
        self.max = max
        self.step = step

    def get_list(self):
        return list(range(self.min, self.max + 1, self.step))

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["min"], data["max"], data["step"])


class ListConfig(dict):
    def __init__(
        self,
        values: Optional[list[Union[list[int], RangeConfig]]],
        str_format: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        values: Optional[list[Union[list[int], RangeConfig]]]
            list of values each value an be either a list of integers or a `RangeConfig`
            object.
            If not specified, it will automatically fill based on the number of CPUs.
            JSON example: `"values": [ [5, 6], {"min": 1, "step": 1, "max": 3 }, [12] ]`
        str_format: Optional[str]
            A formatting string. Used to convert the values into string.
            JSON example: `"str_format": "127.0.0.{i}"`
            with this string the values `i` is replaced by an integer from values
            and the list become:
            `["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.5", "127.0.0.6", "127.0.0.12"]`
        -
        """
        super().__init__(vals=values, str_format=str_format)
        self.vals = values
        self.str_format = str_format

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data.get("values"), data.get("str_format"))

    def get_list(self, core_count: int = 1):
        combined_lists = []

        if not self.vals:
            cpu_count = os.cpu_count()
            if not cpu_count:
                cpu_count = 1

            max_cpus = max(1, int(cpu_count / core_count))
            step = None

            if max_cpus > 8 and max_cpus % 8 == 0:
                step = 8

            if not step:
                step = max_cpus

            while (step > 1) and (max_cpus / step) < 4:
                step = int(step / 2)

            while (max_cpus / step) > 8:
                step *= 2

            for cpu in range(step, max_cpus + 1, step):
                combined_lists.append(cpu)

            combined_lists.append(1)
            combined_lists.append(max_cpus)

        else:
            for cfg in self.vals:

                if isinstance(cfg, list):
                    combined_lists.extend(cfg)
                elif isinstance(cfg, dict):
                    rangecfg = RangeConfig.from_dict(cfg)
                    combined_lists.extend(rangecfg.get_list())
                else:
                    bm_log(
                        f"I cannot handle {type(cfg)}, skipping this item",
                        LogType.ERROR,
                    )

        # make sure there are no duplicated items
        unique_list = sorted(set(combined_lists))
        if self.str_format is not None:
            unique_list[:] = [self.str_format.format(i=i) for i in unique_list]
        return unique_list
