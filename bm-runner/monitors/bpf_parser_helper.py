# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import re

from utils.logger import bm_log, LogType

class BPFParserHelper:
    @staticmethod
    def symbol_to_factor(sym :str) -> int:
        ext = {
            "":1,
            "K":1000,
            "M":1000000,
            "G":1000000000,
            "T":1000000000000,
            "P":1000000000000000,
            }
        return ext[sym]


    @staticmethod
    def get_range_max(range: str) -> int:
        range_pattern = re.compile(r'\[([0-9]+)([A-Z]*), ([0-9]+)([A-Z]*)\)')
        range_match = range_pattern.match(range)
        if not range_match:
            bm_log(f"Range did not match: {range}", LogType.FATAL)
            return 0


        range_min = int(range_match.group(1))
        mul_min = BPFParserHelper.symbol_to_factor(range_match.group(2))
        range_max = int(range_match.group(3))
        mul_max = BPFParserHelper.symbol_to_factor(range_match.group(4))

        return (range_max*mul_max)-1


    @staticmethod
    def get_range_avg(range: str) -> int:
        range_pattern = re.compile(r'\[([0-9]+)([A-Z]*), ([0-9]+)([A-Z]*)\)')
        range_match = range_pattern.match(range)
        if not range_match:
            bm_log(f"Range did not match: {range}", LogType.FATAL)
            return 0

        range_min = int(range_match.group(1))
        mul_min = BPFParserHelper.symbol_to_factor(range_match.group(2))
        range_max = int(range_match.group(3))
        mul_max = BPFParserHelper.symbol_to_factor(range_match.group(4))

        range_avg = range_min + (range_max - range_min)/2

        return range_avg*mul_max
