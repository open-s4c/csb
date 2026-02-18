# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
from bm_utils import resolve_path


def csb_dir() -> Path:
    return Path(os.getcwd()).parent


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
