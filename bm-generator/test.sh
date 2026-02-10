#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e

STRACE_LOG="ls.log"
strace -o ${STRACE_LOG} -a 1 -s 65500 -v -xx -f -Xraw ls

 ./00_init.sh
 ./01_build.sh
 ./02_parse.sh ${STRACE_LOG}
 ./03_extract.sh
 ./04_prepare.sh
 ./05_generate.sh
