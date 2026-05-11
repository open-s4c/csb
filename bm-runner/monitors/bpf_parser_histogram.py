# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import pandas as pd
from io import StringIO
import re

from monitors.bpf_parser import BPFParser
from monitors.bpf_parser_helper import BPFParserHelper

class BPFParserHistogram(BPFParser):
    @staticmethod
    def parse(filename) -> pd.DataFrame:
        # Initialize empty lists to store data
        records = []
        # Regular expressions to match different parts of the data
        map_pattern = re.compile(rf'@[a-zA-Z_]+:')
        range_pattern = re.compile(r'(\[[0-9A-Z, ]+\)) +(\d+) \|')
        map_found = False

        try:
            f = open(filename, "r")
        except IOError:
            return pd.DataFrame([])
        with f:
            data = f.read()
            # Process each line
            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check for PID line
                map_match = map_pattern.fullmatch(line)
                if map_match:
                    map_found = True
                    continue
                
                # Check for range line
                range_match = range_pattern.match(line)
                if range_match and map_found:
                    range_str = range_match.group(1)
                    count = int(range_match.group(2))
                    records.append({
                        'range': range_str,
                        'count': count
                    })
        return pd.DataFrame(records)
    
    @staticmethod
    def results_min_max_avg(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        if df.empty:
            return BPFParser.default_min_max_avg(csv_key)
        
        minimum = float("inf")
        maximum = 0
        num_values = 0
        weighted_total = 0
        for range_str, count in df[["range", "count"]].itertuples(index=False, name=None):
            count = int(count)
            if count < 1:
                continue
            range_avg = BPFParserHelper.get_range_avg(range_str)
            weighted_total += range_avg * count
            num_values += count
            if range_avg < minimum:
                minimum = range_avg
            if range_avg > maximum:
                maximum = range_avg

        if num_values == 0:
            return BPFParser.default_min_max_avg(csv_key)

        average = weighted_total / num_values

        if minimum > maximum:
            minimum = maximum

        result =  csv_key + "_min" + "=" + str(minimum) + ";"
        result += csv_key + "_avg" + "=" + str(average) + ";"
        result += csv_key + "_max" + "=" + str(maximum) + ";"
        return result

    @staticmethod
    def results_histogram(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        if df.empty:
            return BPFParser.default_histogram(csv_key)
        
        result = ""
        cols = range(0, 60)  # TODO: align bm_visualize.py
        hist_list = [0]*60
        for range_str, count in df[["range", "count"]].itertuples(index=False, name=None):
            count = int(count)

            if count < 1:
                continue

            range_max = BPFParserHelper.get_range_max(range_str)
            found_bucket = False
            bucket_min = 0
            bucket_max = 2
            for i in cols:
                bucket_value = 0
                range_max_old = 0
                bucket_max, bucket_min = (
                    bucket_max * 2,
                    bucket_max + 1,
                )

                if range_max <= bucket_max:
                    hist_list[i] += count
                    found_bucket = True
                    break
            if not found_bucket:
                hist_list[cols.stop-1] += count

        for value in hist_list:
            result += str(value) + ","

        result = result.strip(",")
        result = csv_key + "_histogram" + "=" + result + ";"
        return result
