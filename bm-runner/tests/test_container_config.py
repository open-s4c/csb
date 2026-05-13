# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from config.container import ContainersConfig
from utils.logger import bm_log


def test_gen_container_list_defaults():
    container_cfg = ContainersConfig()
    min_steps = container_cfg.MIN_NUM_STEPS
    max_steps = container_cfg.MAX_NUM_STEPS

    # alias private function
    gen_list = getattr(container_cfg, "_ContainersConfig__gen_container_list")

    # Test: list length matches requested steps
    for steps in range(1, int((min_steps + max_steps) / 2) + 1):
        container_counts = gen_list(steps)
        bm_log(f"steps={steps} ({len(container_counts)} tests): {container_counts}")
        assert len(container_counts) == steps, f"Failed for steps={steps}"

    # Test: common core counts produce expected length and first element
    # this is the case we care about the most
    common_core_counts = [6, 8, 12, 16, 24, 32, 88, 96, 160, 192, 256, 320, 384, 512]
    for num_cores in common_core_counts:
        container_counts = gen_list(num_cores)
        bm_log(f"num_cores={num_cores} ({len(container_counts)} tests): {container_counts}")
        assert len(container_counts) >= min_steps, f"Failed for num_cores={num_cores}"
        assert len(container_counts) <= max_steps + 2, f"Failed for num_cores={num_cores}"
        assert (
            container_counts[0] == 1
        ), f"First element should be 1 for num_cores={num_cores}: {container_counts}"
        assert (
            container_counts[-1] == num_cores
        ), f"Last element should be num_cores={num_cores}, container_list: {container_counts}"
    # Test: numbers less than number of steps
    cores_per_container_list = [1, 2, 3, 4, 7]
    for num_cores in common_core_counts:
        for cores_per_container in cores_per_container_list:
            max_containers = num_cores // cores_per_container
            container_counts = gen_list(max_containers)
            bm_log(
                f"max_containers={max_containers} ({len(container_counts)} tests): {container_counts}"
            )
            assert (
                container_counts[0] == 1
            ), f"First element should be 1 for num_cores={num_cores}, cores_per_container={cores_per_container}: {container_counts}"
            assert len(container_counts) <= max_steps + 2, f"Failed for max_containers={num_cores}"

    # There are edge cases that we don't have specific expectations for.
