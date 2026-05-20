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


# TODO: add compare to baseline
# TODO: generate in linux fashion

BENCHMARK_FIELD     = 'algo_name'
THROUGHPUT_FIELD    = 'throughput_min'
COUNT_FIELD         = 'container_cnt'
SUCCESS_FIELD       = 'univ_succ_percent'
COMPARISON_FIELD    = 'kernel'
EXEC_ENV_FIELD      = 'execution_type'
MEASUREMENT_FIELD   = 'throughput_avg' # auto-computed
LINEARITY_FIELD     = 'linearity' # auto-computed


COMPARISON_FILED_PRETTY_NAME = {
    'Linux localhost 6.6.0-138.0.0.119.oe2403sp3.x86_64  1 SMP Wed Feb  4 22:31:12 CST 2026 x86_64 x86_64 x86_64 GNU/Linux' : 'AMD 6.6.0 138',
    'Linux k920b 6.6.0ext4noprof  9 SMP Thu Apr  9 15:34:24 CEST 2026 aarch64 aarch64 aarch64 GNU/Linux': 'k920b 6.6.0'
}

def to_pretty_name(ugly:str) -> str:
    v =  COMPARISON_FILED_PRETTY_NAME.get(ugly, ugly)
    print(v)
    return v



linearity = ""

group_by_fields : list[str] = [BENCHMARK_FIELD, EXEC_ENV_FIELD, 'hostname', COMPARISON_FIELD, 'nb_threads']


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
        assert 'throughput_avg' == MEASUREMENT_FIELD
        baseline = per_run.loc[per_run[COUNT_FIELD] == min_container, MEASUREMENT_FIELD].iloc[0]

        per_run[LINEARITY_FIELD] = per_run[MEASUREMENT_FIELD]/baseline
        results.append(per_run)


    return results

def generate_patch_measurement(df, bm_name, env=""):
    subjects = df[COMPARISON_FIELD].unique()

    # Map original subjects to pretty names
    pretty_mapping = {s: to_pretty_name(s) for s in subjects}

    # Pivot table
    table = df.pivot_table(
        index=COUNT_FIELD,
        columns=COMPARISON_FIELD,
        values=MEASUREMENT_FIELD
    ).reset_index()

    # Flatten MultiIndex if it exists (common with pivot_table)
    if isinstance(table.columns, pd.MultiIndex):
        table.columns = [col[1] if col[1] else col[0] for col in table.columns]

    # Rename columns to pretty names immediately
    table.rename(columns=pretty_mapping, inplace=True)

    # Keep COUNT_FIELD + pretty columns
    pretty_subjects = [pretty_mapping[s] for s in subjects]
    table = table[[COUNT_FIELD] + pretty_subjects]

    # Inject improvement column between first two pretty-named columns
    if len(pretty_subjects) >= 2:
        first, second = pretty_subjects[:2]
        table['diff_%'] = ((table[second] - table[first]) / table[first] * 100).round(6)

    # Convert to Markdown and write
    md_table = table.to_markdown(index=False, tablefmt="grid")
    md_info  = f"- {bm_name}\n"
    md_info  += f"- Execution environment: {env}\n"

    write_to_file(dir=output_dir_name, fname=f"{bm_name}-{env}.txt", content=md_info + md_table)

def generate_comparison_plot(df, bm_name, y='linearity', y_lbl='Linearity', env=""):
    plot_cfg =  PlotConfig(
        hue="kernel",
        hue_lbl="Kernel",
        y=y,
        y_lbl=y_lbl,
        x=COUNT_FIELD,
        x_lbl="#Executions Units",
        title=f"{bm_name}({env})",
    )
    plot_chart(plot=plot_cfg, df=df, out_fig_name=f"{output_dir_name}/{bm_name}-{env}-{y_lbl}")


def add_to_linearity_summary(df, bm, env, idx, tolerance=0.1) -> str:
    """
    Summarize linearity of a benchmark across kernels.

    Args:
        df: DataFrame containing at least COUNT_FIELD, COMPARISON_FIELD, LINEARITY_FIELD
        bm: Benchmark name
        env: Execution environment
        tolerance: Allowed deviation from perfect linearity (1.0)

    Returns:
        A one-line summary string.
    """
    summary = f"## {idx}. {bm} ({env})\n"
    summary += f"|{COMPARISON_FIELD} | Linear | Drops at|\n"
    summary += f"|--- |--- |---|\n"

    for kernel, g in df.groupby(COMPARISON_FIELD):
        g_sorted = g.sort_values(COUNT_FIELD)
        baseline = g_sorted[LINEARITY_FIELD].iloc[0]
        drops = g_sorted[g_sorted[LINEARITY_FIELD] < 1 - tolerance]
        summary += f'|{kernel}|'

        if drops.empty:
            summary += f'✔️|-|\n'
        else:
            first_drop_cnt = drops[COUNT_FIELD].iloc[0]
            first_drop_val = drops[LINEARITY_FIELD].iloc[0]
            summary += f'❌|{first_drop_cnt} (linearity={first_drop_val:.2f})|\n'

    return summary


def compare(df) -> str:
    benchmarks = df[BENCHMARK_FIELD].unique()
    envs = df[EXEC_ENV_FIELD].unique()
    benchmarks.sort()
    Linearity_md = "# Linearity Summary\n"
    idx = 1
    # get all results mapped to a certain benchmark
    for bm in benchmarks:
        for env in envs:
            bm_df = df[(df[BENCHMARK_FIELD] == bm) &
                    (df['execution_type'] == env)]
            if env == 'ExecutionType.CONTAINER':
                nice_env = "container"
            else:
                nice_env = "native"
            generate_patch_measurement(bm_df, bm, env=nice_env)
            generate_comparison_plot(bm_df, bm, y=MEASUREMENT_FIELD, y_lbl="Throughput Average", env=nice_env)
            generate_comparison_plot(bm_df, bm, y="success_avg", y_lbl="Success Average (%)", env=nice_env)
            generate_comparison_plot(bm_df, bm, env=nice_env)
            Linearity_md+=add_to_linearity_summary(bm_df, bm, env=nice_env, idx=idx, tolerance=0.1)
        idx+=1

    write_to_file(Linearity_md, "linearity.md", output_dir_name)

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


