#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

if [ $# -lt 4 ]; then
    echo "Usage: $0 <PORT> <CLIENT_COUNT> <CLIENT_PATH> <META_PATH#1> <META_PATH#2> ..."
    exit 1
fi

IP="127.0.0.1"
START_PORT=$1
CLIENT_COUNT=$2
CLIENT_PATH=$3

# Shift away the first 3 arguments
shift 3

# Remaining arguments are the meta paths
META_PATHS=("$@")

# If fewer meta paths than CLIENT_COUNT, repeat the last one
if [ "${#META_PATHS[@]}" -ne "$CLIENT_COUNT" ]; then
    echo "[ERROR]: Expected $CLIENT_COUNT meta paths, got ${#META_PATHS[@]}"
    exit 1
fi

# TODO: check if meta string is empty
# TODO: create an analogous case for CLIENT_SEQ
# TODO: make it decide whether to launch a client or a server based on
# the available sequence
for ((i=0; i<$CLIENT_COUNT; i++)); do
    port=$((START_PORT + i))
    metafile="${META_PATHS[$i]}"
    # grep everything after `=` and between quotes `"..."`
    # WARNING multiple sequences "", "", "" are not handled
    META_STRING=$(grep '^SERVER_SEQ=' $metafile | sed 's/^SERVER_SEQ="\([^"]*\)"/\1/')
    echo "Launching client#$i on port $port, with meta $metafile"
    $CLIENT_PATH "-R" "-h" "$IP" "-p$port" "-P$META_STRING" &
done

echo "Waiting for clients to finish..."
wait
echo "Clients are done"
