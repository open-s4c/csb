#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e

scriptpath=$(dirname "$0")

input_dir="$1"
output_dir="$2"
filter_file="$3"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "usage: $0 input-directory output-directory"
    exit 1
fi

if [ -z "$FLAMEGRAPH" ]; then
    echo "Please specify the path to FlameGraph toolkit via FLAMEGRAPH environment variable."
    exit 1
fi

mkdir -p "$output_dir"

find "$input_dir" -name flamegraph.stacks | while read n; do
    suffname=$(echo "$n" | sed -e "s#${input_dir}[/]\?##g" | cut -d/ -f2-)
    i=$(echo "$n" | sed -e "s#${input_dir}[/]\?##g" | cut -d/ -f1)
    suff=$(dirname "$suffname")
    appname=$(jq -r '.[0].app' "$input_dir/$i/$suff/experiment_results.json")

    # If user provides a file with selected microbenchmarks, skip those not in the file
    if [ -n "$filter_file" ] && ! grep -q "$appname$" "$filter_file"; then
	continue
    fi
    "$scriptpath/filter-merge-single.sh" "$input_dir/$i/$suff/perf.data" "${appname:0:15}";
done | "$FLAMEGRAPH"/stackcollapse-perf.pl | tee "$output_dir"/all.html.stacks | "$FLAMEGRAPH"/flamegraph.pl --width 1920 > "$output_dir/all.html"
