#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier:
echo "Cleaning up temp folders under $1"
sudo rm -rf $1/syzkaller_min*
