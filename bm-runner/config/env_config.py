# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
from enum import Enum


class UniversalConfig(str, Enum):
    """
    CSB bm-runner has universal configuration that can overwrite default
    behavior and JSON config values. These are set via environment variables,
    and are read at runtime.

    Members
    ----------
    CSB_NO_CLEAN_BENCH: When set to `true`, it disables the cleaning of the build folder of builtin benchmarks.
    CSB_ANALYZE: When set to `false`, it disables the analysis monitors.
    """

    CSB_NO_CLEAN_BENCH = "CSB_NO_CLEAN_BENCH"
    CSB_ANALYZE = "CSB_ANALYZE"


class EnvUniversalConfig:
    DEFAULT_ENV_CONFIG: dict[UniversalConfig, bool] = {
        UniversalConfig.CSB_NO_CLEAN_BENCH: False,
        UniversalConfig.CSB_ANALYZE: True,
    }
    TRUE_VALS: set[str] = {"true", "1", "yes", "on"}

    @staticmethod
    def __read_env_var(env_var: UniversalConfig) -> bool:
        value = os.getenv(env_var.value)
        if value is not None:
            return value.lower() in EnvUniversalConfig.TRUE_VALS
        return EnvUniversalConfig.DEFAULT_ENV_CONFIG[env_var]

    @staticmethod
    def is_on(env_var: UniversalConfig) -> bool:
        return EnvUniversalConfig.__read_env_var(env_var)
