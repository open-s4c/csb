# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
from bm_utils import resolve_path, ensure_exists


def csb_dir() -> Path:
    return Path(os.getcwd()).parent


#################################
# resolve_path tests
#################################
def test_resolve_path_native():
    parent = csb_dir()
    input = "build/bench/x"
    expected_out = os.path.join(parent, input)
    out = resolve_path(input)
    assert expected_out == out


def test_resolve_path_container():
    input = "build/bench/x"
    expected_out = os.path.join("/home", input)
    out = resolve_path(input, use_in_container=True)
    assert expected_out == out


def test_resolve_path_native_full():
    parent = csb_dir()
    relative = "scripts/plugins/launch-clients-local.sh"
    input = os.path.join(parent, relative)
    expected_out = input
    out = resolve_path(input)
    assert expected_out == out


def test_resolve_path_container_full():
    parent = csb_dir()
    relative = "scripts/plugins/launch-clients-local.sh"
    input = os.path.join(parent, relative)
    expected_out = os.path.join("/home", relative)
    out = resolve_path(input, use_in_container=True)
    assert expected_out == out


#################################
# ensure_exists tests
#################################


def test_ensure_exists_relative():
    input_path = "scripts"
    input_name = "prepare.sh"
    expected = "scripts/prepare.sh"
    actual = ensure_exists(name=input_name, dir=input_path)
    assert actual == expected


def test_ensure_exists_sys_wide():
    input_name = "ls"
    input_path = "/tmp"
    expected = "ls"
    actual = ensure_exists(name=input_name, dir=input_path)
    assert actual == expected


def test_ensure_exists_sys_wide_no_dir():
    input_name = "ls"
    expected = "ls"
    actual = ensure_exists(name=input_name)
    assert actual == expected


def test_ensure_exists_env_var():
    input_env_var = "CSB_PLUGINS"
    current_dir = os.getcwd()
    real_dir = f"{current_dir}/../scripts"
    os.environ[input_env_var] = real_dir
    input_name = "prepare.sh"
    input_path = "/tmp"
    expected = os.path.join(real_dir, input_name)
    actual = ensure_exists(name=input_name, dir=input_path, env_var_dir=input_env_var)
    assert actual == expected
