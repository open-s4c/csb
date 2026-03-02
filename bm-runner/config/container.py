# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from typing import Optional
from config.list import ListConfig
import docker
import docker.errors
import os
import sys
from utils.logger import bm_log, LogType
from utils.platform import get_os, OperatingSystem


class ContainersConfig(dict):
    CONFIG_KEY: str = "containers"
    DEFAULT_IMG: dict[OperatingSystem, str] = {
        OperatingSystem.openEuler: "hub.oepkgs.net/openeuler/openeuler",
        OperatingSystem.Ubuntu: "ubuntu:latest",
        OperatingSystem.Unsupported: "ubuntu:latest",
    }

    def __init__(
        self,
        build: Optional[ListConfig] = None,
        container_list: ListConfig = ListConfig(values=[[1]]),
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
        core_affinity_offsets: Optional[ListConfig] = core_count * [0, 1, 2, 3, ...]
            Specifies the cores that should be assigned to the containers.
            Note that the assignment of cores happens in ascending order by default.
        core_count: int
            Number of cores to assign to each container.
        name: str
            The base name of the container.
        image: Optional[str] = same as the host OS e.g. ubuntu:latest on Ubuntu.
            The docker image name to use.
        build: Optional[ListConfig] = list[str]
            Dockerfile build instructions to build the container.
        port: Optional[int]
            The starting port number to use for the first container.
            Subsequent containers will use incremented port numbers.
            This configuration is relevant for networking benchmarks.
        -
        """
        super().__init__(image=image, name=name, core_count=core_count, port=port)
        self.container_list = ListConfig.from_dict(container_list).get_list()
        self.core_count = core_count
        self.core_affinity_offsets = (
            ListConfig.from_dict(core_affinity_offsets).get_list()
            if core_affinity_offsets is not None
            else [core_count * i for i in range(0, self.container_list[-1])]
        )
        self.build = build
        self.image = image if image is not None else self.DEFAULT_IMG[get_os()]
        bm_log(f"Selected image {self.image}", LogType.INFO)
        self.name = name
        self.port = port
        self.__ensure_img_exists()

    def get_container_cnt_list(self) -> list[int]:
        return self.container_list

    def get_core_affinity_offset_list(self) -> list[int]:
        return self.core_affinity_offsets

    def __build(self, client):
        #
        # Step 1: Create a dockerfile from config.build
        #

        # A temporary file name
        dockerfile = "/tmp/.csb_dockerfile"

        # Shall point to the root CSB directory
        path = os.path.abspath(os.path.dirname(__file__) + "../../..")

        lines = [f"FROM {self.image}"]
        if self.build:
            lines += self.build

        with open(dockerfile, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        bm_log(f"Dockerfile written to {dockerfile}")

        #
        # Step 2: Build a container from a Dockerfile
        #

        self.image = "csb_build:latest"

        bm_log(f"Building image '{self.image}'")

        try:
            image, logs = client.images.build(
                tag=self.image,
                dockerfile=dockerfile,
                path=path,
                rm=True,
            )
        except docker.errors.BuildError as e:
            for chunk in e.build_log:
                if "stream" in chunk:
                    sys.stdout.write(chunk["stream"])
            raise

        bm_log(f"Image built: {image.tags}")

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

        if self.build:
            self.__build(client)

        try:
            client.images.get(self.image)
        except docker.errors.ImageNotFound:
            self.__pull_image()
