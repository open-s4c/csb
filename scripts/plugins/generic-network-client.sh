#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

if [ $# -ne 4 ]; then
    echo "Usage: $0 <PORT> <CLIENT_COUNT> <CLIENT_PATH> <META_PATH>"
    exit 1
fi

START_PORT=$1
CLIENT_COUNT=$2
CLIENT_PATH=$3
META_PATH=$4
IP="127.0.0.0"

# grep everything after `=` and between quotes `"..."`
# WARNING multiple sequences "", "", "" are not handled
META_STRING=$(grep '^SERVER_SEQ=' $META_PATH | sed 's/^SERVER_SEQ="\([^"]*\)"/\1/')
echo $META_STRING
# TODO: check if meta string is empty
# TODO: create an analogous case for CLIENT_SEQ
# TODO: make it decide whether to launch a client or a server based on
# the available sequence
for ((i=0; i<$CLIENT_COUNT; i++)); do
    port=$((START_PORT + i))
    echo "Launching client $i on port $port"
    $CLIENT_PATH "-R" "-h" "$IP" "-p$port" "-P$META_STRING" &
done

echo "\nwaiting for clients to finish..."
wait
echo "Clients are done"
