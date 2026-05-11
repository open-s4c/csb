# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import pandas as pd

class BPFParser:
    # @staticmethod
    # def parse(filename) -> pd.DataFrame:
    #     pass

    # @staticmethod
    # def results_min_max_avg(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
    #     pass

    @staticmethod
    def results_histogram(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        pass

    @staticmethod
    def default_min_max_avg(csv_key: str) -> str:
        result =  csv_key + "_min" + "=" + str(0) + ";"
        result += csv_key + "_avg" + "=" + str(0) + ";"
        result += csv_key + "_max" + "=" + str(0) + ";"
        return result

    @staticmethod
    def default_histogram(csv_key: str) -> str:
        empty = ["0"]*60
        result = ",".join(empty)
        result = csv_key + "_histogram" + "=" + result + ";"
        return result