# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Optional
from config.env_config import EnvUniversalConfig, UniversalConfig
import os


class Monitor:
    def __init__(self, dir, args):
        self.dir = dir
        self.args = args

    def get_cpus(self) -> Optional[list[int]]:
        if EnvUniversalConfig.is_on(UniversalConfig.CSB_PIN_MONITORS):
            cpu_count = os.cpu_count()
            if cpu_count is not None:
                return [cpu_count - 1]
        return None

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def collect_results(self) -> str:
        pass
