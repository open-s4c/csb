#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT
set -e

if [ ! -d results ] || [ ! -d bm-runner ] || [ ! -d ./scripts/fg-diff ] || [ ! -d deps ]; then
    echo "Run this script from the CSB directory"
    exit 1;
fi
export FLAMEGRAPH="$(realpath ./deps/FlameGraph)"

export CSB_NO_CLEAN_BENCH=1
for i in $*; do
    ./scripts/fg-diff/run-single.sh $(realpath "$i")
done

source ./venv/bin/activate

mkdir -p ./bench-select
echo "Preprocessing perf.data files from benchmark results"
./scripts/fg-diff/filter-all.sh ./results/ ./bench-select
echo "Calculating difference between flamegraphs"
./scripts/fg-diff/diff-all.sh ./bench-select > ./bench-select/diff.csv
python3 ./scripts/fg-diff/diffset.py --cutoff 5 --input ./bench-select/diff.csv
