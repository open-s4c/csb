#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

PACKET_SPEC="2r1023-1w32"
PORT=5000

./server -p $PORT -P $PACKET_SPEC -O &
SERVER_PID=$!

./client -h localhost -p $PORT -P $PACKET_SPEC -O &
CLIENT_PID=$!

wait $CLIENT_PID
CLIENT_RET=$?

wait $SERVER_PID
SERVER_RET=$?


if [ $SERVER_RET -eq 0 ] && [ $CLIENT_RET -eq 0 ]; then
  echo "[PASS] Both processes completed successfully!"
  exit 0
else
  echo "[FAIL]Client return $CLIENT_RET, Server return $SERVER_RET"
  exit 1
fi





