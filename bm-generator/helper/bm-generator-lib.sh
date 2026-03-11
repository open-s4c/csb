#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

get_workspace_dir() {
    RES_DIR="gen-ws"
    if [ -n "$CSB_RESULTS_GROUP" ]; then
        RES_DIR="$CSB_RESULTS_GROUP"
    fi
    echo "$RES_DIR"
}
