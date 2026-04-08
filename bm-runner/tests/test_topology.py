from utils.topology import Topology
from config.policy import CoreAssignPolicy, PackGroup, CpuOrder
from benchkit.shell.shell import shell_out
from pathlib import Path
import os
from unittest.mock import patch
import pytest

def __mock_read_info(self) -> list[str]:
    print(csb_dir())
    cpu_info = shell_out(
        "cat tests/lscpu_mock.csv",
        print_output=False,
        print_file_shell_cmd=False,
    )
    lines = cpu_info.strip().split("\n")
    print("mock method is called")
    return lines

@pytest.fixture
def mock_read_info(mocker):
    return mocker.patch.object(Topology, '_Topology__read_info', __mock_read_info)


def test_default(mock_read_info):
    topology = Topology()
    policy = CoreAssignPolicy()
    count = 1000
    cpu_list = topology.select(count=count, policy=policy)
    assert len(cpu_list) == count, "Less CPUs returned than requested!"


