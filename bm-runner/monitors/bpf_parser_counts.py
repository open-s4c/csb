# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import re
import pandas as pd
from io import StringIO

from monitors.bpf_parser import BPFParser

class BPFParserCounts(BPFParser):
    @staticmethod
    def extract_pid(line:str) ->int:
        return int(re.search(r'(\d+)', line)[1])

    @staticmethod
    def parse(filename) -> pd.DataFrame:
        try:
            f = open(filename, "r")
        except IOError:
            return pd.DataFrame([])
        with f:
            data = f.read()
            if "ERROR:" in data or "Error attach" in data or "cannot attach" in data or "entry may not exist" in data:
                return pd.DataFrame([])
            if not data.strip():
                return pd.DataFrame([])
            df = pd.read_csv(StringIO(data), sep=': ', header=None, names=['PID', 'Count'], engine='python')
            df['PID'] = df['PID'].map(BPFParserCounts.extract_pid)
            return df

    @staticmethod
    def results_min_max_avg(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        if df.empty:
            return BPFParser.default_min_max_avg(csv_key)
        
        minimum = float("inf")
        maximum = 0
        num_values = 0
        average = 0
        for pid, count in df[["PID", "Count"]].itertuples(index=False, name=None):
            pid = int(pid)
            count = int(count)
            if PIDs and (pid not in PIDs):
                continue
            average *= (num_values / (num_values + 1))
            average += count * (1 / (num_values + 1))
            num_values += 1
            if count < minimum:
                minimum = count
            if count > maximum:
                maximum = count
        
        if num_values == 0:
            return BPFParser.default_min_max_avg(csv_key)

        if minimum > maximum:
            minimum = maximum
        result =  csv_key + "_min" + "=" + str(minimum) + ";"
        result += csv_key + "_avg" + "=" + str(average) + ";"
        result += csv_key + "_max" + "=" + str(maximum) + ";"
        return result

    @staticmethod
    def results_histogram(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        return BPFParser.default_histogram(csv_key)
