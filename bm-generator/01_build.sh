#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


GOBIN="`go env GOBIN`"

if [ "x${GOBIN}" == "x" ]; then
  echo "Set GOBIN go environment variable and add it to PATH"
  echo "Example:"
  echo "  go env -w GOBIN=${HOME}/.local/bin"
  echo "Double check that GOBIN is in $PATH"
  echo "  echo $PATH | grep `go env GOBIN`"
  exit 1
fi

SCRIPT_SYZ_SRC="helper/find_syzkaller_src.sh"
 : ${DIR_SYZ_SRC:=$(${SCRIPT_SYZ_SRC})}

if [ ! -d "${DIR_SYZ_SRC}" ]; then
  echo "syzkaller source dir not found."
  echo "  Building syzkaller with cmake ..."
  cmake -S../ -B../build -DCSB_BM_GENERATOR=ON
  DIR_SYZ_SRC=$(${SCRIPT_SYZ_SRC})
  if [ ! -d "${DIR_SYZ_SRC}" ]; then
    echo "Failed setting up syzkaller sources."
    echo "If the syzkaller source dir is not beneath $(pwd)/build, then run this script as:"
    echo "  DIR_SYZ_SRC=</path/to/syzkaller/source> $0"
    exit 1
  fi
fi

cmake --build ../build --target syzkaller
