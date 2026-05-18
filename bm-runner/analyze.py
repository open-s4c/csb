#!/usr/bin/env python3
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT
import os
import pandas as pd
from utils.logger import bm_log, LogType
from bm_visualize import plot_chart, dump_graphs_to_doc, create_mean_plot, _add_css_style
from config.plot import PlotConfig, PlotType
import sys
from dominate import document

# TODO: maybe it is best to compare with container count
# TODO: add compare to baseline
# TODO: generate in linux fashion

group_by_fields : list[str] = ['algo_name', 'execution_type', 'hostname', 'kernel', 'nb_threads']
avg_fields: list[str] = ['univ_succ_percent', 'throughput_min']

output_dir_name = "analysis-results"


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

def write_to_file(content, fname, dir):
    os.makedirs(dir, exist_ok=True)
    file_path = os.path.join(dir, fname)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def process(file:str) -> list:
    tolerance = 0.1  # 10% tolerance
    results = []
    try:
        df = pd.read_csv(
            file, sep=";", comment="#", engine="python", on_bad_lines="error"
        )
        grouped = df.groupby(group_by_fields)
        for key_group, g in grouped:
            per_run = g.groupby('container_cnt').agg(
                throughput_avg=('throughput_min', 'mean'),
                univ_succ_percent=('univ_succ_percent', 'mean')
            ).reset_index()  # container_cnt becomes a column


            for idx, col in enumerate(group_by_fields):
                per_run[col] = key_group[idx]
            results.append(per_run)
    except Exception as e:
        bm_log(f"{e} on {file}", LogType.ERROR)

    return results

def generate_patch_measurement(df, bm_name):
    subjects = df['kernel'].unique()
    table = df.pivot_table(
        index='container_cnt',
        columns='kernel',
        values='throughput_avg'
    ).reset_index()

    table = table[['container_cnt'] + list(subjects)]
    md_table = table.to_markdown(index=False)

    md_info  = f"# {bm_name}\n"

    write_to_file(dir=output_dir_name, fname=f"{bm_name}.md", content=md_info + md_table)

def generate_comparison_plot(df, bm_name):
    plot_cfg =  PlotConfig(
        hue="kernel",
        hue_lbl="Kernel",
        y="throughput_avg",
        y_lbl="Throughput Average",
        x="container_cnt",
        x_lbl="#Executions Units",
    )
    plot_chart(plot=plot_cfg, df=df, out_fig_name=f"{output_dir_name}/{bm_name}")


def compare(df) -> str:
    benchmarks = df['algo_name'].unique()
    benchmarks.sort()
    # get all results mapped to a certain benchmark
    for bm in benchmarks:
        bm_df = df[(df['algo_name'] == bm) &
                   (df['execution_type'] == 'ExecutionType.CONTAINER')]
        generate_patch_measurement(bm_df, bm)
        generate_comparison_plot(bm_df, bm)

if __name__ == "__main__":
    folder = "/home/lilith/workspace/csb-analyze"
    files = get_all_files_by_ext(folder)
    bm_log(f"Running analysis on {folder}. {len(files)} CSV files detected ...", LogType.INFO)
    all = []
    for f in files:
        res = process(f)
        all.extend(res)

    final_df =  pd.concat(all, ignore_index=True)
    md_table = final_df.to_markdown(index=False)

    per_bm = compare(final_df)
    csv  = final_df.to_csv(index=False)

    write_to_file(dir=".", fname="results.md", content=md_table)
    write_to_file(dir=".", fname="results.csv", content=csv)

    doc = document()
    _add_css_style(doc)
    dump_graphs_to_doc(output_dir_name, doc)
    write_to_file(dir=".", fname="results.html", content=doc.render())

