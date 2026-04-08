# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import pandas as pd

class BPFParser:
    @staticmethod
    def parse(filename) -> pd.DataFrame:
        pass

    @staticmethod
    def results_min_max_avg(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        pass

    @staticmethod
    def results_histogram(df: pd.DataFrame, PIDs: list[int], csv_key: str) ->str:
        pass