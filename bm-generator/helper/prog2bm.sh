#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


if [ $# != 1 ]; then
  echo "Usage: $0 </path/to/syz/prog/file>"
  exit 1
fi

FILEPROG="$1"

if [ ! -f "${FILEPROG}" ]; then
  echo "syz-lang program file ${FILEPROG} does not exist!"
  exit 1
fi

SCRIPT_SYZ_SRC="helper/find_syzkaller_src.sh"
 : ${DIR_SYZ_SRC:=$(${SCRIPT_SYZ_SRC})}

if [ ! -d "${DIR_SYZ_SRC}" ]; then
  echo "syzkaller source dir not found. Try to run:"
  echo "  ./`ls -1 01_*.sh`"
  echo ""
  echo "If the syzkaller source dir is not beneath $(pwd), then run this script as:"
  echo "  DIR_SYZ_SRC=\"</path/to/syzkaller/source>\" $0"
  exit 1
fi

PROG="`basename ${FILEPROG} .prog`"

# TODO: sync. with the definition in cmake `set(SUBDIR "gen-ws")`
DIR_TARGETS="../bench/targets/gen-ws/syz"

DIR_TARGETS_ABS="`readlink -e ${DIR_TARGETS}`"
FILEPROG_ABS="`readlink -e ${FILEPROG}`"

cd "${DIR_SYZ_SRC}"
echo "Converting ${PROG} to benchmark framework"
bin/syz-prog2c -csb -trace=true -format=false -prog "${FILEPROG_ABS}" -cfile "${DIR_TARGETS_ABS}/${PROG}.h"
