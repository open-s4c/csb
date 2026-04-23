# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from utils.topology import Topology
from config.policy import CoreAssignPolicy, PackGroup
from benchkit.shell.shell import shell_out
import pytest


# To be able to test different outputs
# we mock the output of lscpu by using
# existing files
def __read(file) -> list[str]:
    cpu_info = shell_out(
        f"cat tests/{file}",
        print_output=False,
        print_file_shell_cmd=False,
    )
    lines = cpu_info.strip().split("\n")
    return lines


# use hyper threading lscpu mock
def __mock_read_info(self) -> list[str]:
    return __read("lscpu_mock.csv")


# use no hyper threading lscpu mock
def __mock_read_info_no_ht(self) -> list[str]:
    return __read("lscpu_mock_no_ht.csv")


@pytest.fixture
def mock_read_info(mocker):
    return mocker.patch.object(Topology, "_Topology__read_lscpu_info", __mock_read_info)


@pytest.fixture
def mock_read_info_no_ht(mocker):
    return mocker.patch.object(Topology, "_Topology__read_lscpu_info", __mock_read_info_no_ht)


# ensure on default setting we get
# the requested count of cpus
def test_default_count(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy()
    count = 1000
    for count in 1000, 1:
        cpu_list = topology.select(count=count, policy=policy)
        assert len(cpu_list) == count, "Less CPUs returned than requested!"


# ensure we get the requested count of cpus
# if a preselected list is provided
def test_pre_select_count(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy()
    cores = [1, 5, 6]
    for count in 10, 1:
        cpu_list = topology.select(count=count, policy=policy, pre_selected=cores)
        assert len(cpu_list) == count, "Less CPUs returned than requested!"
        if count > len(cores):
            assert set(cpu_list) == set(cores), "Unexpected cores are used"


# check counts match expectation
# the expectation depends on the mock file
# with hyper-threading
def test_stats(mock_read_info):
    topology = Topology()
    exp_cpu_count = 320
    assert exp_cpu_count == topology.get_cpu_count()
    exp_core_count = 160
    assert exp_core_count == topology.get_core_count()
    exp_numa_count = 4
    assert exp_numa_count == topology.get_numa_count()
    exp_pkg_count = 2
    assert exp_pkg_count == topology.get_package_count()


def verify_lists(topo: Topology):
    exp_cpu_list = list(range(0, topo.get_cpu_count()))
    assert exp_cpu_list == topo.get_cpus()
    exp_cores_list = list(range(0, topo.get_core_count()))
    assert exp_cores_list == topo.get_cores()
    exp_numa_list = list(range(0, topo.get_numa_count()))
    assert exp_numa_list == topo.get_numas()
    exp_pkg_list = list(range(0, topo.get_package_count()))
    assert exp_pkg_list == topo.get_packages()


# check lists match expectation
# the expectation depends on the mock file
# with hyper-threading
def test_lists(mock_read_info):
    topology = Topology()
    verify_lists(topology)


def test_numa_pack(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy(pack_group=PackGroup.NUMA)
    count = 80
    actual = topology.select(count=count, policy=policy)
    # note this is valid because we expect NUMA zero to be selected
    # if that assumption breaks the expectation needs to be updated accordingly
    expected = list(range(0, count))
    assert actual == expected


# verify the output when one NUMA without hyper-threading is selected
def test_numa_pack_skip_ht(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy(pack_group=PackGroup.NUMA, one_cpu_per_core=True)
    count = 80
    actual = topology.select(count=count, policy=policy)
    # note this is valid because we expect NUMA zero,
    # and the first CPU from each core  to be selected
    # if that assumption breaks the expectation needs to be updated accordingly
    expected = [x for x in range(0, count) if x % 2 == 0]
    assert set(actual) == set(expected)


def test_pkg_pack(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy(pack_group=PackGroup.PACKAGE)
    count = 160
    actual = topology.select(count=count, policy=policy)
    # note this is valid because we expect package zero to be selected
    # if that assumption breaks the expectation needs to be updated accordingly
    expected = list(range(0, count))
    assert actual == expected


# check counts match expectation
# the expectation depends on the mock file
# without hyper-threading
def test_stats_no_ht(mock_read_info_no_ht):
    topology = Topology()
    exp_cpu_count = 256
    assert exp_cpu_count == topology.get_cpu_count()
    exp_core_count = 256
    assert exp_core_count == topology.get_core_count()
    exp_numa_count = 2
    assert exp_numa_count == topology.get_numa_count()
    exp_pkg_count = 2
    assert exp_pkg_count == topology.get_package_count()


# check lists match expectation
# the expectation depends on the mock file
# without hyper-threading
def test_lists_no_ht(mock_read_info_no_ht):
    topology = Topology()
    verify_lists(topology)


# check distant policy behaves
# as expected
def test_distant(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy(pack_group=PackGroup.DISTANT)
    cpu_count = topology.get_cpu_count()
    for count in 2, 40, 7, 310, cpu_count:
        cpu_list = topology.select(count=count, policy=policy)
        assert len(cpu_list) == count
        assert cpu_list[0] == 0
        assert cpu_list[count - 1] == cpu_count - 1
        # take the distance between the first two
        distance = cpu_list[1] - cpu_list[0]
        # verify they are at equal distance +-1
        for i in range(1, len(cpu_list)):
            assert cpu_list[i] - cpu_list[i - 1] in (distance - 1, distance, distance + 1)
