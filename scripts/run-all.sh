#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e

# examples:
#   scripts/run-all.sh # runs everything under config
#   scripts/run-all.sh *sql* # runs all with config matching *sql*

# Configure the venv
if [ ! -d venv ]; then
    ./scripts/prepare.sh
fi

. ./venv/bin/activate

if [ $# -eq 0 ]; then
    REGEX="*"
else
    REGEX="$1"
fi

shopt -s globstar
BENCHMARKS_CONFIGS=( config/**/$REGEX.json )

echo "We require sudo to run the benchmarks"
sudo -v  # This will prompt for the sudo password and keep it cached

for CONFIG in ${BENCHMARKS_CONFIGS[@]}; do
    echo "Running: $CONFIG"
    scripts/run-single.sh "$CONFIG"
done
