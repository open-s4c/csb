# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

# This class is responsible of building builtin
# CSB targets/benchmarks

from benchkit.shell.shell import shell_out
import os
from utils.logger import bm_log, LogType
from config.env_config import EnvUniversalConfig, UniversalConfig
from pathlib import Path


class Builder:
    project_dir: Path
    build_dir: str = "build"
    CORES: int = 4
    required_targets: list[str] = ["server", "client", "redis-client"]

    def __init__(self):
        self.project_dir = Builder.get_project_dir()
        self.build_dir = os.path.join(self.project_dir, self.build_dir)

    @staticmethod
    def get_project_dir() -> Path:
        return Path(os.getcwd()).parent

    def __run_cmake_config(self):
        cmd = f"cmake -DCMAKE_BUILD_TYPE=Release -S{self.project_dir} -B{self.build_dir}"
        shell_out(cmd, output_is_log=False, print_file_shell_cmd=False)

    def __clean_build_dir(self):
        if EnvUniversalConfig.is_on(UniversalConfig.CSB_NO_CLEAN_BENCH):
            return
        shell_out(f"rm -rf {self.build_dir}/*", output_is_log=False, print_file_shell_cmd=False)

    def build(self):
        if EnvUniversalConfig.is_on(UniversalConfig.CSB_NO_BUILD_BENCH):
            bm_log(
                "CSB_NO_BUILD_BENCH is set to true, skipping building all benchmarks. Users should manually have them built",
                LogType.WARNING,
            )
            return
        self.__clean_build_dir()
        self.__run_cmake_config()
        cmd = f"cmake --build {self.build_dir} -j {self.CORES}"
        shell_out(cmd, output_is_log=True, print_file_shell_cmd=False)

    def __build_target(self, target):
        cmd = f"cmake --build {self.build_dir} --target {target} -j {self.CORES}"
        shell_out(cmd, output_is_log=True, print_file_shell_cmd=False)

    def build_target(self, target):
        self.__clean_build_dir()
        self.__run_cmake_config()
        for t in self.required_targets:
            self.__build_target(t)
        self.__build_target(target)

    def __get_targets(self) -> set[str]:
        self.__run_cmake_config()
        cmd = f"cmake --build {self.build_dir} --target help"
        output = shell_out(
            cmd, print_shell_cmd=False, print_output=False, print_file_shell_cmd=False
        )
        try:
            # Split output by lines and remove the first line and '... ' from each target
            lines = output.splitlines()
            # Skip the first line, and strip the '... ' from each subsequent line, adding them to a set (hashset)
            targets = {line.strip()[4:] for line in lines[1:] if line.strip().startswith("...")}
            return targets
        except Exception as e:
            bm_log(f"Failed to parse list of targets from cmake. {e}", LogType.ERROR)
            return set()

    def target_exists(self, target: str) -> bool:
        targets = self.__get_targets()
        return target in targets
