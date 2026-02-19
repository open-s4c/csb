# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from benchkit.shell.shell import shell_out
import os
import sys
import time
from typing import Optional
from abc import abstractmethod

from config.plugin import ExecutionTime
import bm_config
from config.application import Application
from config.benchmark import ExecutionType
from bm_utils import is_port_free_to_use
from monitors.monitor_factory import MonitorFactory
from utils.logger import bm_log, LogType
from bm_utils import resolve_path


class ExecutionUnit:
    START_FILE = f"{Application.BUILTIN_APP_DIR}/start"
    RETRY_COUNT = 16 * 60  # 16 mins
    CMD_WHILE_NOT_START = f"for i in $(seq 1 $((10 * RETRY_COUNT))); do if [ -e {START_FILE} ]; then break; fi; sleep 0.1; done;"

    def __init__(self, idx, home_dir, app: Application, type: ExecutionType):
        self.app = app
        self.idx = idx
        self.type = type
        self.home_dir = home_dir
        self.name = "C" if type == ExecutionType.CONTAINER else "N"
        self.name += f"{idx:03d}_{app.name}"
        self.output_file = os.path.join(Application.BUILTIN_APP_DIR, self.name)

    @abstractmethod
    def exec(self, command):
        pass

    @abstractmethod
    def wait(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    def get_output(self) -> str:
        line = open(resolve_path(self.output_file), "r").read()
        # If there is an adapter, it means that
        # the applications' output needs to be transformed
        # after collection. This is important to have
        # a format complying to dict `key=val;...`
        if self.app.adapter is not None:
            line = self.app.adapter.adapt(line)
        return f"execution_unit={self.name};app={self.app.name};{line}"


class Executer:
    SLEEP_IN_SEC = 5

    def __init__(self, home_dir, results_dir):
        assert bm_config.g_config
        self.home_dir = home_dir
        self.results_dir = results_dir
        self.exec_units = []
        self.plugins = bm_config.g_config.get_plugins()
        self.nics = bm_config.g_config.get_nics()
        self.monitors = [
            MonitorFactory.create(monitor_type=type, results_dir=results_dir, args=args)
            for type, args in bm_config.g_config.get_benchmark_cfg().monitors.items()
        ]

    def __call_plugins(self, exec_time):
        plugins = [plugin for plugin in self.plugins if plugin.exec_time == exec_time]
        for plugin in plugins:
            plugin.execute(
                self.results_dir,
                n_units=len(self.exec_units),
                homedir=self.home_dir,
                res_dir=self.results_dir,
            )

    def __stop_plugins(self):
        for plugin in self.plugins:
            plugin.stop()

    def __start_monitors(self):
        for monitor in self.monitors:
            monitor.start()

    def __stop_monitors(self):
        for monitor in self.monitors:
            monitor.stop()

    def exec_all(self, threads, duration, noise, initial_size, port_start: Optional[int]):
        try:
            for idx, eu in enumerate(self.exec_units):
                if port_start is not None:
                    sz = idx + port_start
                    # TODO: At the moment initial_size is exploited to pass the port number,
                    # make sure that initial_size is not used when port is available
                    # or find a proper way to pass the port number to the micro-bm
                    if not is_port_free_to_use(sz):
                        bm_log(
                            f"Port {sz} is already in use!, make sure ports in this range [{port_start}:{len(self.exec_units)-1}] are free to use.",
                            LogType.FATAL,
                        )
                        sys.exit(1)
                else:
                    sz = initial_size
                eu.exec(
                    eu.app.get_cmd(
                        threads=threads,
                        duration=duration,
                        noise=noise,
                        initial_size=sz,
                        index=idx,
                        work_dir=self.home_dir,
                    )
                )
            # give start signal
            self.signal_start()
            # wait for all containers to finish
            for eu in self.exec_units:
                eu.wait()
        finally:
            self.cleanup()

    def collect_results(self) -> str:
        stat_prefix = "".join([monitor.collect_results().strip() for monitor in self.monitors])
        result = "".join(f"{stat_prefix}{eu.get_output()}" for eu in self.exec_units)
        return result

    def signal_start(self):
        bm_log(f"Waiting for {self.SLEEP_IN_SEC}, before giving the start signal")
        time.sleep(self.SLEEP_IN_SEC)
        self.__call_plugins(ExecutionTime.PRE)
        self.__start_monitors()
        shell_out(
            f"touch {ExecutionUnit.START_FILE}",
            current_dir=self.home_dir,
            output_is_log=False,
        )
        self.__call_plugins(ExecutionTime.POST)

    def cleanup(self):
        bm_log("cleaning up, stopping all processes/containers")
        for eu in self.exec_units:
            eu.stop()
        start_file = resolve_path(ExecutionUnit.START_FILE)
        if os.path.exists(start_file):
            os.remove(start_file)
        self.__stop_monitors()
        self.__call_plugins(ExecutionTime.CLEANUP)
        self.__stop_plugins()
