#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

if [ $# -ne 4 ]; then
    echo "Usage: $0 <PORT> <AGENT_COUNT> <AGENT_PATH> <META_PATH>"
    exit 1
fi

IP="127.0.0.1"
START_PORT=$1
AGENT_COUNT=$2
AGENT_PATH=$3
META_PATH=$4

SERVER=$(grep -E '^SERVER_SEQ=' "$META_PATH")
CLIENT=$(grep -E '^CLIENT_SEQ=' "$META_PATH")

# Validate: exactly one must exist
if [ -n "$SERVER" ] && [ -n "$CLIENT" ]; then
    echo "Error: Both SERVER_SEQ and CLIENT_SEQ are present. Only one allowed."
    exit 2
fi

if [ -z "$SERVER" ] && [ -z "$CLIENT" ]; then
    echo "Error: Neither SERVER_SEQ nor CLIENT_SEQ found. One is required."
    exit 2
fi

# Set variable based on which one exists
if [ -n "$SERVER" ]; then
    NETWORKING_AGENT="client"
    SEQ_VALUE=$(echo "$SERVER" | sed -E 's/^SERVER_SEQ="?([^"]*)".*/\1/')
else
    NETWORKING_AGENT="server"
    SEQ_VALUE=$(echo "$CLIENT" | sed -E 's/^CLIENT_SEQ="?([^"]*)".*/\1/')
fi
echo "$SEQ_VALUE"
for ((i=0; i<$AGENT_COUNT; i++)); do
    port=$((START_PORT + i))
    echo "Launching [$NETWORKING_AGENT] Agent#$i on port $port, with meta $META_PATH"
    $AGENT_PATH/$NETWORKING_AGENT "-R" "-h" "$IP" "-p$port" "-P$SEQ_VALUE" &
done

echo "Waiting for networking agents to finish..."
wait
echo "Networking agents are done."
