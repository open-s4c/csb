from enum import Enum

class PackGroup(str, Enum):
    PACKAGE = "package"
    NUMA = "numa"
    NO_PACK = "none"

class CpuOrder(str, Enum):
    ASC = "asc"
    DESC  = "desc"

class CoreAssignPolicy(dict):
    def __init__(
        self,
        pack_group: PackGroup = PackGroup.NO_PACK,
        cpu_order: CpuOrder = CpuOrder.ASC,
        one_cpu_per_core: bool = False
    ):
        super().__init__(
        pack_group=pack_group, cpu_order=cpu_order, one_cpu_per_core=one_cpu_per_core)
        self.pack_group = pack_group
        self.cpu_order = cpu_order
        self.one_cpu_per_core = one_cpu_per_core

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["pack_group"], data["cpu_order"], data["one_cpu_per_core"])

