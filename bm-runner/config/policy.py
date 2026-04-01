from enum import Enum
class CoreAssignPolicy(str, Enum):
    MAX_DISTANCE = "max_distance"       # Spread across NUMA → L3 → cores → SMT
    SPREAD_NUMA = "spread_numa"        # Prefer different NUMA nodes
    PACK_NUMA = "pack_numa"          # Prefer same NUMA node
    SPREAD_L3 = "pack_l3"           # Prefer different L3 cache groups
    AVOID_SMT = "void_smt"          # Avoid SMT siblings
    EVEN_ONLY = "even"         # Only even-numbered CPUs
    ODD_ONLY = "odd"           # Only odd-numbered CPUs
