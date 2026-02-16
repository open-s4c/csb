#!/usr/bin/env bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

for f in config/*.json; do
    # Check if the JSON file is valid.
    if jq empty "$f"; then
        # Format valid JSON file
        jq . "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    else
        echo "[ERROR] $f is invalid JSON! Fix it!"
        exit 1
    fi
done

