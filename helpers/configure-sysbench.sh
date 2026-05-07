#!/bin/sh
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

set -e
SCRIPT_DIR="$(readlink -f $(dirname "$0")/../bm-external)"

mkdir -p ${SCRIPT_DIR}
(
	cd ${SCRIPT_DIR}
	if [ ! -e sysbench/.git ]; then
		git clone https://github.com/akopytov/sysbench
	else
	    (cd sysbench && make clean|| true)
	fi
	cd sysbench
	./autogen.sh
	./configure --with-mysql --with-pgsql --prefix=${SCRIPT_DIR}/sysbench
	make
	make install
)
