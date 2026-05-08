# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from config.container import ContainersConfig


def test_gen_container_list_defaults():
    container_cfg = ContainersConfig()
    num_steps = 16

    # alias private function once
    gen_list = container_cfg._ContainersConfig__gen_container_list  # type: ignore[attr-defined]

    # Test: list length matches requested steps
    for steps in range(1, num_steps + 1):
        container_counts = gen_list(steps)
        assert len(container_counts) == steps, f"Failed for steps={steps}"

    # Test: common core counts produce expected length and first element
    common_core_counts = [32, 96, 384, 192, 256, 320, 160]
    for num_cores in common_core_counts:
        container_counts = gen_list(num_cores)
        assert len(container_counts) == num_steps + 1, f"Failed for num_cores={num_cores}"
        assert container_counts[0] == 1, f"First element should be 1 for num_cores={num_cores}"

    # Test: numbers less than number of steps
    cores_per_container_list = [2, 3, 7]
    for num_cores in common_core_counts:
        for cores_per_container in cores_per_container_list:
            max_containers = num_cores // cores_per_container
            container_counts = gen_list(max_containers)
            assert (
                container_counts[0] == 1
            ), f"First element should be 1 for num_cores={num_cores}, cores_per_container={cores_per_container}"

