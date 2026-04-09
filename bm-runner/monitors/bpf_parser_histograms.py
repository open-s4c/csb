# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import pandas as pd
from io import StringIO
import re

from monitors.bpf_parser import BPFParser
from monitors.bpf_parser_helper import BPFParserHelper

class BPFParserHistograms(BPFParser):
    @staticmethod
    def parse(filename) -> pd.DataFrame:
        # Initialize empty lists to store data
        records = []
        current_pid = None
        # Regular expressions to match different parts of the data
        pid_pattern = re.compile(rf'@[a-zA-Z_]+\[(\d+)\]:')
        range_pattern = re.compile(r'(\[[0-9A-Z, ]+\)) +(\d+) \|')

        try:
            f = open(filename, "r")
        except IOError:
            return None
        with f:
            data = f.read()
            # Process each line
            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check for PID line
                pid_match = pid_pattern.fullmatch(line)
                if pid_match:
                    current_pid = pid_match.group(1)
                    continue
                
                # Check for range line
                range_match = range_pattern.match(line)
                if range_match and current_pid:
                    range_str = range_match.group(1)
                    count = int(range_match.group(2))
                    records.append({
                        'pid': current_pid,
                        'range': range_str,
                        'count': count
                    })
        return pd.DataFrame(records)

    @staticmethod
    def results_min_max_avg(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        if df == None:
            return BPFParser.default_min_max_avg(csv_key)

        minimum = 2^62
        maximum = 0
        num_values = 0
        average = 0
        for values in df.itertuples():
            # print(values)
            pid = values[1]
            range_str = values[2]
            # print(range_str)
            count = int(values[3])
            if count < 1:
                continue
            if PIDs and pid not in PIDs:
                continue
            average *= (num_values / (num_values + count))
            range_avg = BPFParserHelper.get_range_avg(range_str)
            # print(range_avg)
            average += range_avg * ((count * count) / (num_values + count))
            num_values += count
            if range_avg < minimum:
                minimum = range_avg
            if range_avg > maximum:
                maximum = range_avg

        if minimum > maximum:
            minimum = maximum

        result =  csv_key + "_min" + "=" + str(minimum) + ";"
        result += csv_key + "_avg" + "=" + str(average) + ";"
        result += csv_key + "_max" + "=" + str(maximum) + ";"
        return result

    @staticmethod
    def results_histogram(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        if df == None:
            return BPFParser.default_histogram(csv_key)

        result = ""
        cols = range(0, 60)  # TODO: align bm_visualize.py
        hist_list = [0]*60
        for values in df.itertuples():
            pid = int(values[1])
            range_str = values[2]
            count = int(values[3])

            if count < 1:
                continue
            if PIDs and (pid not in PIDs):
                continue

            range_max = BPFParserHelper.get_range_max(range_str)
            found_bucket = False
            bucket_min = 0
            bucket_max = 2
            for i in cols:
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

        # hist_list[0] = 10
        for value in hist_list:
            result += str(value) + ","

        result = result.strip(",")
        result = csv_key + "_histogram" + "=" + result + ";"
        # print("Histograms result:")
        # print(result)
        return result

