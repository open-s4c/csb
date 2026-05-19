#!/usr/bin/env python3
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT
import os
import argparse
import pandas as pd
from utils.logger import bm_log, LogType
from bm_visualize import plot_chart, dump_graphs_to_doc, create_mean_plot, _add_css_style
from config.plot import PlotConfig, PlotType
import sys
from dominate import document
from bm_utils import write_to_file, get_all_files_by_ext, read_data_frame_from_csv
from datetime import datetime

# TODO: maybe it is best to compare with container count
# TODO: add compare to baseline
# TODO: generate in linux fashion

BENCHMARK_FIELD     = 'algo_name'
THROUGHPUT_FIELD    = 'throughput_min'
COUNT_FIELD         = 'container_cnt'
SUCCESS_FIELD       = 'univ_succ_percent'
LINEARITY_FIELD     = 'linearity'


group_by_fields : list[str] = [BENCHMARK_FIELD, 'execution_type', 'hostname', 'kernel', 'nb_threads']


output_dir_name = "analysis-results"

def create_output_dir() -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")  # Format: YYYYMMDD_HHMMSS
    dir = f"analysis-results-{timestamp}"
    os.makedirs(dir, exist_ok=True)
    return dir

def process(file:str) -> list:
    tolerance = 0.1  # 10% tolerance
    results = []
    df = read_data_frame_from_csv(file)
    if df is None:
        return []

    grouped = df.groupby(group_by_fields)
    for key_group, g in grouped:
        per_run = g.groupby(COUNT_FIELD).agg(
            throughput_avg=(THROUGHPUT_FIELD, 'mean'),
            success_avg=(SUCCESS_FIELD, 'mean')
        ).reset_index()  # container_cnt becomes a column


        for idx, col in enumerate(group_by_fields):
            per_run[col] = key_group[idx]

        min_container = per_run[COUNT_FIELD].min()
        baseline = per_run.loc[per_run[COUNT_FIELD] == min_container, 'throughput_avg'].iloc[0]

        per_run[LINEARITY_FIELD] = per_run['throughput_avg']/baseline
        results.append(per_run)


    return results

def generate_patch_measurement(df, bm_name):
    subjects = df['kernel'].unique()
    table = df.pivot_table(
        index=COUNT_FIELD,
        columns='kernel',
        values='throughput_avg'
    ).reset_index()

    table = table[[COUNT_FIELD] + list(subjects)]
    md_table = table.to_markdown(index=False)

    md_info  = f"# {bm_name}\n"

    write_to_file(dir=output_dir_name, fname=f"{bm_name}.md", content=md_info + md_table)

def generate_comparison_plot(df, bm_name, y='linearity', y_lbl='Linearity'):
    plot_cfg =  PlotConfig(
        hue="kernel",
        hue_lbl="Kernel",
        y=y,
        y_lbl=y_lbl,
        x=COUNT_FIELD,
        x_lbl="#Executions Units",
    )
    plot_chart(plot=plot_cfg, df=df, out_fig_name=f"{output_dir_name}/{bm_name}")


def compare(df) -> str:
    benchmarks = df[BENCHMARK_FIELD].unique()
    benchmarks.sort()
    # get all results mapped to a certain benchmark
    for bm in benchmarks:
        bm_df = df[(df[BENCHMARK_FIELD] == bm) &
                   (df['execution_type'] == 'ExecutionType.CONTAINER')]
        generate_patch_measurement(bm_df, bm)
        generate_comparison_plot(bm_df, bm, y="throughput_avg", y_lbl="Throughput Average")
        generate_comparison_plot(bm_df, bm, y="success_avg", y_lbl="Success Average (%)")
        generate_comparison_plot(bm_df, bm)


def get_files(folders):
    all_files = []
    for folder in folders:
        if not os.path.isdir(folder):
            bm_log(f"Skipping {folder}. It is not a valid directory.", LogType.ERROR)
            continue
        files = get_all_files_by_ext(folder)
        bm_log(f"Found {len(files)} CSV in {folder}.")
        all_files.extend(files)
    return all_files


if __name__ == "__main__":
    """
    """
    parser = argparse.ArgumentParser(
        description="Process one or more folders."
    )
    parser.add_argument(
        "folders",
        nargs="+",  # One or more arguments
        help="Path(s) to folder(s) to process"
    )
    args = parser.parse_args()
    output_dir_name = create_output_dir()

    # process
    files = get_files(args.folders)
    bm_log(f"Processing {len(files)} files", LogType.INFO)
    all = []
    for f in files:
        res = process(f)
        all.extend(res)

    final_df =  pd.concat(all, ignore_index=True)
    md_table = final_df.to_markdown(index=False)

    per_bm = compare(final_df)
    csv  = final_df.to_csv(index=False)

    write_to_file(dir=output_dir_name, fname="results.md", content=md_table)
    write_to_file(dir=output_dir_name, fname="results.csv", content=csv)

    doc = document()
    _add_css_style(doc)
    dump_graphs_to_doc(output_dir_name, doc)
    write_to_file(dir=output_dir_name, fname="results.html", content=doc.render())
    bm_log(f"Results written to {output_dir_name}", LogType.INFO)


