#!/bin/bash

 : ${ROCKSDB_DIR:="bm-external/rocksdb"}

rocksdb_exe="${ROCKSDB_DIR}/db_bench"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <command to run>"
  exit 1
fi

if [ ! -f "${rocksdb_exe}" ]; then
  echo "RocksDB executable `db_bench` not found in directory ${ROCKSDB_DIR}."
  exit 1
fi

num=5000000
thr=5
num=$((num / thr))

${ROCKSDB_DIR} --threads=${thr} --num=${num} --db=/tmp/rocksdb_db --benchmarks=fillseq

$@
