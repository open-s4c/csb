#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e

BASE_DIR="$(dirname "$0")/.."
cd $BASE_DIR

info() {
    echo "[prepare.sh] $1"
}

if [ ! -d "deps/benchkit/scripts/install_venv.sh" ]; then
    git submodule update --init --recursive
fi

### Configure the env
if test -d venv; then
    info "benchmark environment already configured"
else
    info "configuring benchmark environment"
    ./scripts/configure.sh
fi
