#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


if [ $# != 1 ]; then
  echo "Usage: $0 </path/to/syz/prog/file>"
  exit 1
fi

PROG="$1"

PROCESSES=1
REPEATS=1
THREADED=false

echo "Converting ${PROG}"
bin/syz-prog2c -format=false -repeat=${REPEATS} -procs ${PROCESSES} -threaded=${THREADED} -prog "${PROG}" 2> "${PROG}".err > "${PROG}".c
