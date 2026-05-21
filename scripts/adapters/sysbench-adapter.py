#!/usr/bin/env python3
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import sys
import re

"""
Convert a sysbench output into a set of key-value pairs.

With that, giving the example below

    sysbench 1.0.20 (using system LuaJIT 2.1.1761727121)

    Running the test with following options:
    Number of threads: 8
    Report intermediate results every 5 second(s)
    Initializing random number generator from current time


    Initializing worker threads...

    Threads started!

    SQL statistics:
        queries performed:
            read:                            17500
            write:                           4998
            other:                           2499
            total:                           24997
        transactions:                        1249   (1242.10 per sec.)
        queries:                             24997  (24858.86 per sec.)
        ignored errors:                      1      (0.99 per sec.)
        reconnects:                          0      (0.00 per sec.)

    General statistics:
        total time:                          1.0051s
        total number of events:              1249

    Latency (ms):
            min:                                    2.88
            avg:                                    6.43
            max:                                   81.58
            95th percentile:                       14.46
            sum:                                 8025.28

    Threads fairness:
        events (avg/stddev):           156.1250/2.09
        execution time (avg/stddev):   1.0032/0.00

would generate an one-line string with:

        number_of_threads=8;\
        sql_statistics.queries_performed.read=17500;\
        sql_statistics.queries_performed.write=4998;\
        sql_statistics.queries_performed.other=2499;\
        sql_statistics.queries_performed.total=24997;\
        ...
        latency.sum=8025.28;threads_fairness.events=156.1250;\
        threads_fairness.execution_time=1.0032

Making it be recognized by CSB.
"""

def parse_sysbench(text):

    results = []
    stack = []

    re_get_name = re.compile(r"(\s*)([^\:]+):\s*([\d\.]*)(?:\b|$)")
    re_parenthesis = re.compile(r"\s*\([^\)]+\)")
    re_special_chr = re.compile(r"\W+")

    for ln in text.splitlines():
        ln = ln.replace('\t', '    ')

        match = re_get_name.match(ln)
        if not match:
            continue

        indent = len(match.group(1))
        name = match.group(2).lower()
        value = match.group(3)

        # Cleanup name
        name = re_parenthesis.sub("", name)
        name = re_special_chr.sub("_", name).strip("_")
        if not name:
            continue

        # Pop old keys
        while stack and stack[-1][0] > indent:
            stack.pop()

        # Update key if same level, or append if deeper
        if stack and stack[-1][0] == indent:
            stack[-1] = (indent, name)
        else:
            stack.append((indent, name))

        if value:
           names = []
           for indent, name in stack:
               names.append(name)

           results.append(".".join(names) + "=" + value)

    return results


if __name__ == '__main__':
    text = sys.stdin.read().strip()
    if not text:
        sys.exit("No input received from STDIN.")

    results = parse_sysbench(text)

    print(";".join(results))
