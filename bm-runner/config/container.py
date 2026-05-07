# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from typing import Optional
from config.list import ListConfig
import docker
import docker.errors
import sys
import math
from utils.logger import bm_log, LogType
from utils.platform import get_os, OperatingSystem
from utils.topology import Topology
from config.policy import CoreAssignPolicy

class ContainersConfig(dict):
    CONFIG_KEY: str = "containers"
    DEFAULT_IMG: dict[OperatingSystem, str] = {
        OperatingSystem.openEuler: "hub.oepkgs.net/openeuler/openeuler",
        OperatingSystem.Ubuntu: "ubuntu:latest",
        OperatingSystem.Unsupported: "ubuntu:latest",
    }

    def __init__(
        self,
        container_list: Optional[ListConfig] = None,
        core_assignment_policy: CoreAssignPolicy = CoreAssignPolicy(),
        core_affinity_offsets: Optional[ListConfig] = None,
        core_count: int = 1,
        name: str = "",
        image: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """
        ContainersConfig represents the configuration for multiple containers.
        Represented as a JSON object.
        Parameters
        ----------
        container_list: ListConfig = {"values": [[1]]}
            Specifies the number of containers to run.
        one_cpu_per_core: bool = False,
        core_assignment_policy: CoreAssignPolicy = {"pack_group":"none", "cpu_order": "asc", "one_cpu_per_core": false}
            Configures the CPU assignment policy, i.e. which CPUs can be assigned to execution units (containers/native processes).
            Note that the policy is overwritten by `core_affinity_offsets`. If the users wish to use this configuration, they
            should make sure not to specify `core_affinity_offsets`.
        core_affinity_offsets: Optional[ListConfig] = core_count * [0, 1, 2, 3, ...]
            Specifies the cores that should be assigned to the containers.
            Note that the assignment of cores happens in ascending order by default.
            This configuration overwrites `core_assignment_policy`.
        core_count: int
            Number of cores to assign to each container.
        name: str
            The base name of the container.
        image: Optional[str] = same as the host OS e.g. ubuntu:latest on Ubuntu.
            The docker image name to use.
        port: Optional[int]
            The starting port number to use for the first container.
            Subsequent containers will use incremented port numbers.
            This configuration is relevant for networking benchmarks.
        -
        """
        super().__init__(
            image=image,
            name=name,
            core_count=core_count,
            port=port,
            core_assignment_policy=core_assignment_policy,
        )
        self.cpus: list[int]
        self.topo = Topology()
        self.core_count = core_count
        self.policy = CoreAssignPolicy.from_dict(core_assignment_policy)
        self.container_list = self.__get_default_container_list() if container_list is None else ListConfig.from_dict(container_list).get_list()
        self.__set_cpus(core_affinity_offsets=core_affinity_offsets)
        self.image = image if image is not None else self.DEFAULT_IMG[get_os()]
        self.name = name
        self.port = port
        self.__ensure_img_exists()

    def __set_cpus(self, core_affinity_offsets):
        """
        Selects which CPUs are allowed to be used according to the
        policy and core_affinity_offsets.
        """
        pre_selected_cpus: Optional[list[int]] = (
            None
            if core_affinity_offsets is None
            else ListConfig.from_dict(core_affinity_offsets).get_list()
        )
        # Calculate the maximum number of CPUs needed.
        # max number of containers * cores per container
        max_cpu_count = max(self.container_list) * self.core_count
        self.cpus = self.topo.select(
            count=max_cpu_count, policy=self.policy, pre_selected=pre_selected_cpus
        )

    def __get_gen_list(self, max, cpus_per_container) -> list[int]:
        num_steps = 16
        if max < num_steps:
            step = 1
        else:
            step = (max // num_steps)

        default_container_list = list(range(0, max+1, step))
        assert default_container_list[0] == 0, "unexpected, given the range starts with zero"
        default_container_list.remove(0)
        if default_container_list[0] != 1:
            default_container_list.insert(0, 1) # replace zero with 1

        bm_log(f"Defined container list with step={step}, cpus_per_contianer={cpus_per_container} to be {default_container_list}", LogType.INFO)
        return default_container_list

    def __get_default_container_list(self) -> list[int]:
        cpus_per_container = self.core_count
        if self.policy.one_cpu_per_core:
            # if hyper-threads are not allowed we define the max
            # based on core count
            max  = math.floor(self.topo.get_core_count() / cpus_per_container)
        else:
            # if hyper-threads are allowed we define it based on the CPU count
            max  = math.floor(self.topo.get_cpu_count() / cpus_per_container)

            return self.__get_gen_list(max=max, cpus_per_container=cpus_per_container)



    def get_container_cnt_list(self) -> list[int]:
        return self.container_list

    def get_cpu_pool(self) -> list[int]:
        """
        Returns the list of CPUs that the benchmark is allowed to use.
        """
        # we use set here, because we don't want duplicated items
        # this is only used for collecting information.
        return list(set(self.cpus))

    def get_cpus(self, eu_idx: int) -> str:
        """
        Returns a list, in string format, of the CPUs that should be assigned
        to the given execution unit (identified by its) index.
        """
        first = eu_idx * self.core_count  # first index
        last = first + self.core_count  # last index (exclusive)
        assert last <= len(self.cpus)
        cpus_lst = self.cpus[first:last]
        cpus_str: str = ",".join(map(str, cpus_lst))
        bm_log(f"Execution Unit#{eu_idx} will be assigned CPUS: {cpus_str}")
        return cpus_str

    def __pull_image(self):
        client = docker.from_env()
        bm_log(f"Docker image {self.image} does not exist. Pulling it now...\n", LogType.INFO)
        try:
            client.images.pull(self.image)
        except Exception as e:
            bm_log(f"Failed to pull image {self.image} with error {str(e)}", LogType.FATAL)
            sys.exit(1)

    def __ensure_img_exists(self):
        client = docker.from_env()
        try:
            client.images.get(self.image)
        except docker.errors.ImageNotFound:
            self.__pull_image()
