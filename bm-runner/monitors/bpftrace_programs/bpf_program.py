# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import Optional
import pandas as pd
import re
from io import StringIO

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

    def gen_program(self) -> str:
        return self.apply_filters(self.program)

    @abstractmethod
    def get_program(self) -> str:
        pass

    @abstractmethod
    def get_out_filename(self) -> str:
        pass

    @abstractmethod
    def collect_results(self, output_dir: str) -> pd.DataFrame:
        pass

    def parse_counts(self, filename) -> pd.DataFrame:
        with open(filename, "r") as f:
            data = f.read()
            df = pd.read_csv(StringIO(data), sep=': ', header=None, names=['PID', 'Count'], engine='python')
            df['PID'] = df['PID'].map(self.extract_pid)
            return df

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

    def df_to_dict(self, df, key, value):
        result = {}
        for index, row in df.iterrows():
            result[row[key]] = row[value] 
        return result

    def extract_pid(self, line:str) ->int:
        return int(re.search(r'(\d+)', line)[1])
