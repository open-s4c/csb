#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

PACKET_SPEC="2r1023-1w32"
NUM_CLIENTS=3
PORT=5000

CLIENT_PIDS=()
# launch clients in the background and save their PIDs
for i in $(seq 1 "$NUM_CLIENTS"); do
  echo "Launching client#$i on port $PORT"
  ./client -h localhost -p $PORT -P $PACKET_SPEC -O -R &
  CLIENT_PIDS+=($!)
done

echo "Launching server on port $PORT"
./server -p $PORT -P $PACKET_SPEC -O &
SERVER_PID=$!

A_CLIENT_FAILED=0
for pid in "${CLIENT_PIDS[@]}"; do
  wait "$pid"
  ret=$?
  echo "Client#$i exited with $ret"
  if [ $ret -ne 0 ]; then
    A_CLIENT_FAILED=1
  fi
done

wait $SERVER_PID
SERVER_RET=$?
echo "Server exited with $SERVER_RET"

if [[ $SERVER_RET =~ ^(0|124)$ ]] && [[ $A_CLIENT_FAILED -eq 0 ]]; then
  exit 0
else
  exit 1
fi





