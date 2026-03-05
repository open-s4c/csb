#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

if [ $# -ne 3 ]; then
    echo "Usage: $0 <PORT> <CLIENT_PATH> <META_PATH>"
    exit 1
fi

PORT=$1
CLIENT_PATH=$2
META_PATH=$3
IP="127.0.0.0"

META_STRING=$(cat "$META_PATH")

${CLIENT_PATH} -R -h ${IP} -p${PORT} -P${META_STRING}
