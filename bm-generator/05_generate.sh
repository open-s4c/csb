#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


cmake -S. -Bbuild
cmake --build build --target csb-generate
cmake --build build --target csb-gen-agg
