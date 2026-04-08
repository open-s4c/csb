from utils.topology import Topology
from config.policy import CoreAssignPolicy
from benchkit.shell.shell import shell_out
import pytest


def __read(file) -> list[str]:
    cpu_info = shell_out(
        f"cat tests/{file}",
        print_output=False,
        print_file_shell_cmd=False,
    )
    lines = cpu_info.strip().split("\n")
    return lines


def __mock_read_info(self) -> list[str]:
    return __read("lscpu_mock.csv")


def __mock_read_info_no_ht(self) -> list[str]:
    return __read("lscpu_mock_no_ht.csv")


@pytest.fixture
def mock_read_info(mocker):
    return mocker.patch.object(Topology, "_Topology__read_info", __mock_read_info)


@pytest.fixture
def mock_read_info_no_ht(mocker):
    return mocker.patch.object(Topology, "_Topology__read_info", __mock_read_info_no_ht)


def test_default_count(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy()
    count = 1000
    cpu_list = topology.select(count=count, policy=policy)
    assert len(cpu_list) == count, "Less CPUs returned than requested!"


def test_pre_select_count(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy()
    cores = [1, 5, 6]
    count = 10
    cpu_list = topology.select(count=count, policy=policy, pre_selected=cores)
    assert len(cpu_list) == count, "Less CPUs returned than requested!"
    assert set(cpu_list) == set(cores), "Unexpected cores are used"


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


def test_lists(mock_read_info):
    topology = Topology()
    verify_lists(topology)


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


def test_lists_no_ht(mock_read_info_no_ht):
    topology = Topology()
    verify_lists(topology)
