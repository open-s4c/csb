#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

awk 'match($0, /([0-9.]+)[[:space:]]+lps/, a) {printf "throughput_lps=%s;\n", a[1]}'
