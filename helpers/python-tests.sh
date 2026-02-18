#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

# Note: run this script from CSB folder `helpers/python-tests.sh`
. ./venv/bin/activate
cd bm-runner
export PYTHONPATH=$(pwd)
pytest -v
