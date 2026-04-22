#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

source helper/bm-generator-lib.sh

if [ $# -lt 1 ]; then
    echo "Usage: $0 <prefix>"
    echo "Regenerates json files based on fg_single.json.in and bm_single.json.in template in <prefix> folders."
    exit 1
fi

DIR_CURRENT="$(pwd)"
CSB_ROOT="$(pwd)/.."

DIR_BUILD="build"

renew_cmake() {
    cd "${CSB_ROOT}"
    cmake -B "${DIR_BUILD}" .
    cd "${DIR_CURRENT}"
}

PREFIXES="$@"

for PREFIX in ${PREFIXES}; do
    export CSB_RESULTS_GROUP="${PREFIX}"
    renew_cmake "${PREFIX}"
    ./05_generate.sh
done