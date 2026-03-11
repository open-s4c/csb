#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


 : ${ROCKSDB_DIR:="bm-external/rocksdb"}

rocksdb_exe="${ROCKSDB_DIR}/db_bench"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <command to run>"
  exit 1
fi

if [ ! -f "${rocksdb_exe}" ]; then
  echo "RocksDB executable db_bench not found in directory ${ROCKSDB_DIR}."
  echo "Check if RocksDB has been succesfully installed, or alter the directory variable ROCKSDB_DIR."
  exit 1
fi

num=5000000
thr=5
num=$((num / thr))

$rocksdb_exe --threads=${thr} --num=${num} --db=/tmp/rocksdb_db --benchmarks=fillseq

$@
