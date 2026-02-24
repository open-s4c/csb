# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from config.env_config import EnvUniversalConfig, UniversalConfig
import os


def del_env_var(env_var: UniversalConfig):
    if env_var.value in os.environ:
        del os.environ[env_var.value]


def test_env_var_dne():
    for env_var in UniversalConfig:
        del_env_var(env_var)
        assert EnvUniversalConfig.is_on(env_var) == EnvUniversalConfig.DEFAULT_ENV_CONFIG[env_var]


def test_env_var_true():
    for env_var in UniversalConfig:
        for val in EnvUniversalConfig.TRUE_VALS:
            os.environ[env_var.value] = val
            assert EnvUniversalConfig.is_on(env_var)
            os.environ[env_var.value] = "false"
            assert not EnvUniversalConfig.is_on(env_var)
