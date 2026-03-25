# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

from abc import abstractmethod

class BPFProgram:
    def __init__(self, dir, args):
        self.dir = dir
        self.args = args

    @abstractmethod
    def get_program(self) -> str:
        pass

    @abstractmethod
    def get_out_filename(self) -> str:
        pass

    @abstractmethod
    def collect_results(self) -> str:
        pass
