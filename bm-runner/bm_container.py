# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

### Reference: https://docker-py.readthedocs.io/en/stable/containers.html
import docker
import docker.errors
import sys
from benchkit.shell.shell import shell_out
from bm_executer import Executer
from bm_executer import ExecutionUnit
import bm_utils
from typing import Optional
from config.container import ContainersConfig
from config.nics import NicsConfig, ContainerNicConfig
from config.application import Application
from config.benchmark import ExecutionType
from utils.logger import bm_log, LogType
from bm_utils import resolve_path


class Container(ExecutionUnit):
    def __init__(
        self,
        idx,
        image,
        home_dir,
        core_set,
        record_data_dir,
        app: Application,
        port: Optional[int] = None,
        nic: Optional[ContainerNicConfig] = None,
    ):
        super().__init__(idx=idx, type=ExecutionType.CONTAINER, home_dir=home_dir, app=app)
        self.client = docker.from_env()  # Initialize Docker client
        self.image = image
        self.core_set = core_set
        self.record_data_dir = record_data_dir
        self.port = port + self.idx if port else None
        self.nic = nic

    def get_results_dir(self) -> str:
        return str(resolve_path(self.record_data_dir, use_in_container=True))

    def wait(self):
        # TODO: wait with a timeout
        container = self.client.containers.get(self.name)
        bm_log(f"Waiting for Container: {self.name} to stop")
        result = container.wait()
        exit_code = result["StatusCode"]
        if exit_code != 0:
            bm_log(
                f"Container: {self.name} has failed/or crashed with exit code {exit_code}",
                LogType.FATAL,
            )
            sys.exit(1)

    def stop(self):
        try:
            container = self.client.containers.get(self.name)
            container.stop()
            container.remove()
            # Remove network namespace as well
            if self.nic:
                shell_out(f"sudo ip netns del {self.name}", ignore_any_error_code=True)
            bm_log(f"Container: {self.name} has been stopped and removed")
        except docker.errors.NotFound:
            pass  # Container does not exist, nothing to do

    def add_nic(self, container):
        assert self.nic is not None
        # find the PID of the initial task of a container.
        pid = docker.APIClient().inspect_container(container.id)["State"]["Pid"]
        netcfg = self.nic
        smp_irq_affinity = (
            netcfg.core_affinity_offset
            if netcfg.core_affinity_offset is not None
            else self.core_set
        )
        # Configure the NIC
        shell_out(
            f"sudo ../scripts/add-nic-to-container.sh {netcfg.nic} {smp_irq_affinity} {pid} {self.name} {netcfg.ip} {netcfg.netmask}"
        )

    def __start(self, commands):
        self.stop()
        try:
            ports = {f"{self.port}/tcp": ("0.0.0.0", self.port)} if self.port else None
            container = self.client.containers.run(
                image=self.image,
                command=["bash", "-c", commands],
                name=self.name,
                cpuset_cpus=self.core_set,
                volumes={
                    f"{self.home_dir}": {"bind": "/home", "mode": "rw"},
                    "/usr": {"bind": "/usr", "mode": "rw"},
                    "/mnt": {"bind": "/mnt", "mode": "rw"},
                    "/lib/modules": {"bind": "/lib/modules", "mode": "rw"},
                    "/etc": {"bind": "/etc", "mode": "rw"},
                },
                privileged=True,  # privileged mode
                detach=True,  # detach mode
                working_dir="/home",
                ports=ports,
            )
            bm_utils.save_container_config(self.record_data_dir, self.name)

            if self.nic:
                self.add_nic(container)

            bm_log(
                f"Container {self.name} is created, will run on {self.idx} => {self.port}, and will run on cores={self.core_set} and waiting for start signal"
            )
        except docker.errors.APIError as e:
            bm_log(f"Could not start container {self.name}: {str(e)}", LogType.ERROR)

    def exec(self, command):
        if self.app.cd:
            assert self.app.path is not None, "path is not set while change directory is requested!"
            command = f"cd {self.app.path} && {command}"
        commands = f"{self.CMD_WHILE_NOT_START} {command} > {resolve_path(self.output_file, use_in_container=True)}"  # same as self.output_file outside container.
        self.__start(commands)


class Containers(Executer):
    def __init__(
        self,
        config: ContainersConfig,
        apps: list[Application],
        home_dir,
        count,
        record_data_dir,
        nics: Optional[NicsConfig] = None,
    ):
        super().__init__(home_dir, results_dir=record_data_dir)
        assert len(apps) == count, "[BUG] Application list length must be equal to count"
        bm_log(f"Initializing {count} containers with config: {config}")
        core_offsets = config.get_core_affinity_offset_list()
        for i in range(count):
            core_set = bm_utils.get_cpu_set(start=core_offsets[i], core_cnt=config.core_count)
            container = Container(
                idx=i,
                home_dir=home_dir,
                image=config.image,
                core_set=core_set,
                record_data_dir=record_data_dir,
                port=config.port,
                app=apps[i],
                nic=self.nics.get_cfg(i) if self.nics else None,
            )
            self.add_exec_unit(container)
