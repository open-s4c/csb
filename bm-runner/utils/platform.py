# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from enum import Enum
from utils.logger import bm_log, LogType


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
