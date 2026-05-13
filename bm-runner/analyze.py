#!/usr/bin/env python3
import os
import pandas as pd
from utils.logger import bm_log, LogType
import sys

group_by_fields : list[str] = ['algo_name', 'execution_type', 'hostname', 'kernel', 'nb_threads']
avg_fields: list[str] = ['univ_succ_percent', 'throughput_min']


# collect all csvs in the given folder
def get_all_files_by_ext(dir:str, extension:str = ".csv"):
    """
    Returns all files under the given dir and subdirs, which have the given file extension.
    """
    filtered_files = []
    for root, _, files  in os.walk(dir):
        for file in files:
            if file.endswith(extension):
                abs_path = os.path.join(root, file)
                filtered_files.append(abs_path)
    return filtered_files

# Allowed CPUs
# kernel
# throughput_min  // avg
# univ_succ_percent
# algo_name
# execution_type // group by

def process(file:str) -> list:
    tolerance = 0.1  # 10% tolerance
    results = []
    try:
        df = pd.read_csv(
            file, sep=";", comment="#", engine="python", on_bad_lines="error"
        )
        grouped = df.groupby(group_by_fields)
        for key_group, g in grouped:
            per_run = g.groupby('container_cnt')

            avg_per_container = per_run['throughput_min'].mean()
            min_container     = avg_per_container.index.min()
            avg_min_throughput = float(avg_per_container[min_container])
            linearity_per_count = avg_per_container / avg_min_throughput

            dropped = linearity_per_count[(linearity_per_count < (1 - tolerance))]
            if dropped.empty:
                checkmark = "✔"
                drop_note = ""
            else:
                checkmark = "✘"
                drop_note = str(dropped.index.min())


            record = {group_by_fields[idx]: value for idx, value in enumerate(key_group)}
            record['linear'] = checkmark
            record['Drops at'] = drop_note
            record['throughput_avg'] = avg_per_container.mean()

            univ_succ_avg = per_run['univ_succ_percent'].mean()  # Series of container averages
            record['univ_succ_percent'] = univ_succ_avg.mean() # scalar average across containers

            results.append(record)
    except Exception as e:
        bm_log(f"{e} on {file}", LogType.ERROR)

    return results

if __name__ == "__main__":
    folder = "/home/lilith/workspace/csb-analyze"
    files = get_all_files_by_ext(folder)
    bm_log(f"Running analysis on {folder}. {len(files)} CSV files detected ...", LogType.INFO)
    all = []
    for f in files:
        res = process(f)
        all.extend(res)

    final_df = pd.DataFrame(all)
    md_table = final_df.to_markdown(index=False)
    csv  = final_df.to_csv(index=False)
    with open("results.md", "w") as f:
         f.write(md_table)
    with open("results.csv", "w") as f:
         f.write(csv)
