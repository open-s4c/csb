#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

duration="$1"
port_offset="$2"
timeout $1 redis-server --port $((port_offset + 8000)) --protected-mode no || true
