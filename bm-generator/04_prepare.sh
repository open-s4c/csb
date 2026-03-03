#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


 : ${DIR_PROG:="./extracted"}
 : ${JOBS:=$(nproc)}

if [ ! -d "${DIR_PROG}" ]; then
    echo "Directory ${DIR_PROG} does not exist."
    echo "Run scripts with lower numbers first, or specify directory explicitly:"
    echo "  DIR_PROG=\"/path/to/prog/files/\" $0"
    exit 1
fi

DIR_TARGETS="../bench/targets/gen-ws/syz"

if [ -d "${DIR_TARGETS}" ]; then
  echo "`readlink -e ${DIR_TARGETS}` exist!"
  echo "[WARNING] Using this directory might lead to unexpected results, please (re)move it before header generation."
fi

mkdir -p "${DIR_TARGETS}"

find "${DIR_PROG}" -type f -name '*.prog' -print0 | xargs -0 -n 1 -P ${JOBS} ./helper/prog2bm.sh
