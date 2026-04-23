# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Optional
from config.env_config import EnvUniversalConfig,UniversalConfig
from utils.logger import bm_log, LogType
import os

class Monitor:
    def __init__(self, dir, args):
        self.dir = dir
        self.args = args

    def get_cpus(self) -> Optional[list[int]]:
        if EnvUniversalConfig.is_on(UniversalConfig.CSB_PIN_MONITORS):
            return [os.cpu_count() - 1]
        else:
            None

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def collect_results(self) -> str:
        pass
