#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


if [ $# -ne 4 ]; then
    echo "Usage: $0 <start_port> <number_of_clients> <start_file> <client_path>"
    exit 1
fi

START_PORT=$1
CLIENT_COUNT=$2
START_FILE=$3
CLIENT_PATH=$4
IP="127.0.0.0"

echo "#of clients: $CLIENT_COUNT"
echo "starting port: $START_PORT"
echo "start file path: $START_FILE"
echo "client search path: $CLIENT_PATH"

while [ ! -e $START_FILE ]; do
    sleep 0.1;
    echo "Waiting for server to start: this file does not exist yet $2"
done;

for ((i=0; i<$CLIENT_COUNT; i++)); do
    port=$((START_PORT + i))
    echo "Launching client $i on port $port"
    $CLIENT_PATH/network/redis-client "$IP" "$port" &
done

echo "\nwaiting for clients to finish..."
wait
echo "Clients are done"
