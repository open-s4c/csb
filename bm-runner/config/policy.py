# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from enum import Enum


class PackGroup(str, Enum):
    """
    Supported groups for packing.

    Members
    ----------
    PACKAGE: Use CPUs that belong to package/socket zero only.
    NUMA: Use CPUs that belong to NUMA/Node zero only.
    DISTANT: [Experimental-feature] Use CPUs at the maximum possible distant from each other.
    NO_PACK: CPUs crossing NUMA and package domains can be chosen.
    """

    PACKAGE = "package"
    NUMA = "numa"
    DISTANT = "distant"
    NO_PACK = "none"


class CpuOrder(str, Enum):
    """
    Supported CPU orders.

    Members
    ----------
    ASC: Assign CPUs in ascending order.
    DESC: Assign CPUs in descending order.
    """

    ASC = "asc"
    DESC = "desc"


class CoreAssignPolicy(dict):
    def __init__(
        self,
        pack_group: PackGroup = PackGroup.NO_PACK,
        cpu_order: CpuOrder = CpuOrder.ASC,
        one_cpu_per_core: bool = False,
    ):
        """
        CPU/Core assignment policy for execution units, i.e. containers and native processes.

        Parameters
        ----------
        pack_group: PackGroup
            Specifies the policy of CPU selection, whether in the same NUMA, same Package,
            can cross packages, or distant.
        cpu_order: CpuOrder
            Specifies the assignment order, whether ascending to starting for CPU lowest index,
            or descending starting from the highest CPU index.
            This configuration is ignored if pack_group is distant.
        one_cpu_per_core: bool
            Whether to use only one CPU from each Core. This is relevant to hyper-threading
            when multiple CPUs share the same core. When set to true, from each core only
            the first CPU is considered.
            This configuration is ignored if pack_group is distant.
        """
        super().__init__(
            pack_group=pack_group, cpu_order=cpu_order, one_cpu_per_core=one_cpu_per_core
        )
        self.pack_group = pack_group
        self.cpu_order = cpu_order
        self.one_cpu_per_core = one_cpu_per_core

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["pack_group"], data["cpu_order"], data["one_cpu_per_core"])
