#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e

info() {
    echo "[run.sh] $1"
}

### Configure the env
if [ ! -d venv ]; then
    info "venv not found. running prepare.sh"
    ./scripts/prepare.sh
fi
. ./venv/bin/activate

# Determine if continue intended
# if a parameter is passed to the script,
# it means the user just wants to regenerate the HTML
# for the given results folder, and the chosen benchmark
if [ $# -eq 0 ]; then
    info "Running benchmarks"
    CONTINUE_BM=""
else
    info "Reproduce the graphs, without rerun"
    CONTINUE_BM="--replot $*"
fi

# detect all available benchmark configurations
BENCHMARKS_CONFIGS=( config/*.json )

echo "The following benchmarks are available, select one to run"

COLUMNS=20
select CONFIG in ${BENCHMARKS_CONFIGS[@]}; do
    if [ ! -z "$CONFIG" ]; then
	TITLE=$(basename "$CONFIG" .json)
	break;
    else
	echo "Invalid index!"
	exit 1
    fi;
done
unset COLUMNS

info "running $TITLE on $CONFIG"
# How to call:
# $ ./run.sh path-to-directory   # to regenerate the plots.
# $ ./run.sh                     # to run the benchmark.
echo scripts/fg-diff/run-single.sh "$CONFIG" $CONTINUE_BM
scripts/fg-diff/run-single.sh "$CONFIG" $CONTINUE_BM
