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

#META_STRING=$(cat "$META_PATH")
# grep everything after = and between quotes!
# WARNING multiple sequences "", "", "" are not handled
META_STRING=$(grep '^SERVER_SEQ=' $META_PATH | sed 's/^SERVER_SEQ="\([^"]*\)"/\1/')
echo $META_STRING
# TODO: check if meta string is empty
# TODO: create an analogous case for CLIENT_SEQ

${CLIENT_PATH} -R -h ${IP} -p${PORT} -P${META_STRING}
