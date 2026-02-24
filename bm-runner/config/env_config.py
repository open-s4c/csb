import os
from enum import Enum

class UniversalConfig(str, Enum):
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
