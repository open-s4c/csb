#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e

# examples:
#   scripts/run-all.sh # runs everything under config
#   scripts/run-all.sh "*sql*" # runs all with config matching *sql*
#   scripts/run-all.sh "*sql*" bm_empty # run configs matching *sql* plus bm_empty

sudo_awake()
{
        while :; do
                sleep 60
                sudo -v
        done
}

terminate()
{
        pkill -SIGINT -P $$
        trap - SIGINT
        exit
}

# Configure the venv
if [ ! -d venv ]; then
    ./scripts/prepare.sh
fi

. ./venv/bin/activate

shopt -s globstar
shopt -s nullglob

BENCHMARKS_CONFIGS=()

if [ $# -eq 0 ]; then
    BENCHMARKS_CONFIGS+=(config/**/*.json)
else
    for pattern in "$@"; do
        pattern="${pattern#config/}"
        pattern="${pattern%.json}"
        BENCHMARKS_CONFIGS+=( config/**/${pattern}.json )
    done
fi

ntests=${#BENCHMARKS_CONFIGS[@]}

if [ ${ntests} -eq 0 ];then
    echo "No tests to run."
   exit 1
fi

echo "We require sudo to run the benchmarks"
sudo -v
sudo_awake &
trap terminate SIGINT ERR EXIT

n=1
for CONFIG in ${BENCHMARKS_CONFIGS[@]}; do
    echo
    echo "======================================================================================="
    echo "${n}/${ntests} running: $CONFIG"
    echo "======================================================================================="
    echo
    scripts/run-single.sh "$CONFIG" || echo -e "=====\nERROR on $CONFIG\n====="
    n=$((n + 1))
done
