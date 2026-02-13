#!/bin/sh
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


set -e

if [ "${STYLE}" != "" ]; then
    STYLE=":${STYLE}"
fi

git ls-files '*.h' '*.c' | grep -v 'deps' | grep -v 'bench/targets/syz/' | xargs -I {} clang-format -style=file${STYLE} -i "$(pwd)/{}"


if [ "${SILENT}" != "true" ]; then
    # Display changed files and exit with 1 if there were differences.
    git --no-pager diff --exit-code
fi
