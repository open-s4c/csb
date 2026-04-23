# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Optional
import os

class Monitor:
    def __init__(self, dir, args):
        self.dir = dir
        self.args = args

    def get_cpus(self) -> Optional[list[int]]:
        return [os.cpu_count() - 1]

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def collect_results(self) -> str:
        pass
