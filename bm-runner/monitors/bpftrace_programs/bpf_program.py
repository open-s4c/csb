# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Optional
import pandas as pd
import re
from io import StringIO
from utils.logger import bm_log, LogType

class BPFProgram:
    program = ""
    cpu = -1
    pid = -1

    def __init__(self, name, dir, args):
        self.dir = dir
        self.args = args[2:]
        self.progname = name
        self.cpu = int(args[0])
        self.pid = int(args[1])

    def _filter_cpu(self, program:str) -> str:
        if self.cpu >= 0:
            return program.replace("__FILTER_CPU__", f"cpu == {self.cpu}")
        else:
            return program.replace("__FILTER_CPU__", "1")
        
    def _filter_pid(self, program:str) -> str:
        if self.pid >= 1:
            return program.replace("__FILTER_PID__", f"pid == {self.pid}")
        else:
            return program.replace("__FILTER_PID__", "1")

    def apply_filters(self, program:str) -> str:
        filtered_program = program
        filtered_program = self._filter_cpu(filtered_program)
        filtered_program = self._filter_pid(filtered_program)
        return filtered_program

    def get_program(self) -> str:
        return self.apply_filters(self.program)

    def get_out_filename(self):
        return self.filename

    def get_csv_key(self):
        return self.csv_key

    @abstractmethod
    def collect_results(self, output_dir: str, PIDs: list[int]) -> str:
        pass

    def get_range_avg(self, range: str) -> int:
        ext = {
            "":1,
            "K":1000,
            "M":1000000,
            "G":1000000000,
            "T":1000000000000,
            "P":1000000000000000,
            }
        range_pattern = re.compile(r'\[([0-9]+)[A-Z]*, ([0-9]+)([A-Z]*)\)')
        range_match = range_pattern.match(range)
        if not range_match:
            bm_log(f"Range did not match: {range}", LogType.FATAL)
            return 0

        range_min = int(range_match.group(1))
        range_max = int(range_match.group(2))

        print(range_min)
        print(range_max)

        range_avg = range_min + (range_max - range_min)/2

        mul = ext[range_match.group(3)]
        return range_avg*mul

    def parse_counts(self, filename) -> pd.DataFrame:
        with open(filename, "r") as f:
            data = f.read()
            df = pd.read_csv(StringIO(data), sep=': ', header=None, names=['PID', 'Count'], engine='python')
            df['PID'] = df['PID'].map(self.extract_pid)
            return df

    def results_counts(self, df: pd.DataFrame, PIDs: list[int]) ->str:
        minimum = 2^62
        maximum = 0
        num_values = 0
        average = 0
        for values in df.itertuples():
            print(values)
            pid = values[0]
            count = values[1]
            if PIDs and pid not in PIDs:
                continue
            average *= (num_values / (num_values + 1))
            average += count * (1 / (num_values + 1))
            num_values += 1
            if count < minimum:
                minimum = count
            if count > maximum:
                maximum = count
        result =  self.get_csv_key() + "_min" + "=" + str(minimum) + ";"
        result += self.get_csv_key() + "_avg" + "=" + str(average) + ";"
        result += self.get_csv_key() + "_max" + "=" + str(maximum) + ";"
        return result

    def parse_histograms(self, filename) -> pd.DataFrame:
        # Initialize empty lists to store data
        records = []
        current_pid = None
        # Regular expressions to match different parts of the data
        pid_pattern = re.compile(rf'@[a-zA-Z]+\[(\d+)\]:$')
        range_pattern = re.compile(r'(\[[0-9A-Z, ]+\)) +(\d+) \|')

        with open(filename, "r") as f:
            data = f.read()
            # Process each line
            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check for PID line
                pid_match = pid_pattern.match(line)
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

    def results_histograms(self, df: pd.DataFrame, PIDs: list[int]) ->str:
        minimum = 2^62
        maximum = 0
        num_values = 0
        average = 0
        for values in df.itertuples():
            print(values)
            pid = values[1]
            range_str = values[2]
            print(range_str)
            count = int(values[3])
            if PIDs and pid not in PIDs:
                continue
            average *= (num_values / (num_values + count))
            range_avg = self.get_range_avg(range_str)
            print(range_avg)
            average += range_avg * ((count * count) / (num_values + count))
            num_values += count
            if range_avg < minimum:
                minimum = range_avg
            if range_avg > maximum:
                maximum = range_avg
        result =  self.get_csv_key() + "_min" + "=" + str(minimum) + ";"
        result += self.get_csv_key() + "_avg" + "=" + str(average) + ";"
        result += self.get_csv_key() + "_max" + "=" + str(maximum) + ";"
        return result

    def parse_histogram(self, filename) -> pd.DataFrame:
        # Initialize empty lists to store data
        records = []
        # Regular expressions to match different parts of the data
        map_pattern = re.compile(rf'@[a-zA-Z]+:$')
        range_pattern = re.compile(r'(\[[0-9A-Z, ]+\)) +(\d+) \|')

        with open(filename, "r") as f:
            data = f.read()
            # Process each line
            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check for PID line
                map_match = map_pattern.match(line)
                if map_match:
                    continue
                
                # Check for range line
                range_match = range_pattern.match(line)
                if range_match and map_match:
                    range_str = range_match.group(1)
                    count = int(range_match.group(2))
                    records.append({
                        'range': range_str,
                        'count': count
                    })
        return pd.DataFrame(records)

    def results_histogram(self, df: pd.DataFrame) ->str:
        minimum = 2^62
        maximum = 0
        num_values = 0
        average = 0
        for values in df.itertuples():
            range_str = values[0]
            count = int(values[1])
            average *= (num_values / (num_values + count))
            range_avg = self.get_range_avg(range_str)
            average += range_avg * ((count * count) / (num_values + count))
            num_values += count
            if range_avg < minimum:
                minimum = range_avg
            if range_avg > maximum:
                maximum = range_avg
        result =  self.get_csv_key() + "_min" + "=" + str(minimum) + ";"
        result += self.get_csv_key() + "_avg" + "=" + str(average) + ";"
        result += self.get_csv_key() + "_max" + "=" + str(maximum) + ";"
        return result

    def df_to_dict(self, df, key, value):
        result = {}
        for index, row in df.iterrows():
            result[row[key]] = row[value] 
        return result

    def extract_pid(self, line:str) ->int:
        return int(re.search(r'(\d+)', line)[1])
