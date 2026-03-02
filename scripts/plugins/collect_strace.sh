#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


FILE_LOG=$1
shift

if [ -z "`command -v strace`" ]; then
  echo "\"strace\" command not found in \$PATH. Either install strace or add it to PATH"
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage:"
  echo "  $0 <output_fname> <command> [<arg1>] [<arg2>] ..."
  exit 1
fi

if [ -f "${FILE_LOG}" ]; then
  echo "Output file \"${FILE_LOG}\" already exists. (re)move it, or use a different output file name. Example:"
  echo "  FILE_LOG=strace_output.log $0 $@"
  exit 1
fi

strace -o "${FILE_LOG}" -a 1 -s 65500 -v -xx -f -Xraw --raw=wait4 $@
