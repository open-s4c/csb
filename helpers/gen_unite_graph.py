#!/usr/bin/env python3
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Read benchmark CSVs, read linearity‑plot definitions from JSON
config files under a given root, generate a PNG for each
`execution_type` that compares the different kernel versions,
and produce a small HTML gallery that shows every image.

The output file names now follow the pattern:
    <app_name>-<execution_type>-<NNN>.png
where NNN is a zero‑padded counter per (app, exec_type) pair.

Example:
    python gen_graph.py ./results/ --config-root ./config/

The first version o this tool was LLM-generated on Ollama on a 16GB DRNA4
VRAM GPU using queries on: gpt-oss, gemma4, nemotron-cascade-2, qwen3.5,
qwen3.6.

Current version was manually adjusted to ensure that the code is working
as expected.
"""

import argparse
import json
import os
import re
import shlex
import sys

from glob import iglob
from textwrap import dedent
from typing import Dict, List, Tuple

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")  # no GUI, pure file output


#
# Data class to store plot parameters obtained from CSB config
#
class PlotParams:
    """Container for seaborn plotting parameters."""

    def __init__(
        self,
        x: str,
        y: str,
        hue: str,
        title: str,
        x_lbl: str = "",
        y_lbl: str = "",
        hue_lbl: str = "",
    ):
        self.x = x
        self.y = y
        self.hue = hue
        self.title = title
        self.x_lbl = x_lbl
        self.y_lbl = y_lbl
        self.hue_lbl = hue_lbl


#
# Helper functions
#
def read_csv_header(filepath: str) -> Tuple[str, str]:
    """
    Pull out kernel_version and campaign_name from CSV header.
    """
    kernel_version = "Unknown"
    campaign_name = None

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("# kernel:"):
                    content = line.replace("# kernel:", "").strip()
                    tokens = shlex.split(content)

                    if len(tokens) >= 3:
                        kernel_version = tokens[2]

                elif line.startswith("# benchmark_campaign_name:"):
                    campaign_name = line.split(":", 1)[1].strip()
    except Exception as e:
        print(f"Warning: Could not read metadata from {filepath}: {e}")

    return kernel_version, campaign_name


def get_csv(filepath: str) -> pd.DataFrame:
    """
    Read a single CSV with pandas.
    Add two extra columns: kernel_version and campain obtained from header
    """
    try:
        df = pd.read_csv(filepath, sep=";", comment="#", engine="python")
    except pd.errors.EmptyDataError:
        return None

    kernel, campaign = read_csv_header(filepath)

    df["kernel_version"] = kernel
    if campaign:
        df["app"] = campaign
    else:
        df["app"] = os.path.splitext(os.path.basename(filepath))[0]

    return df


def clear_string(text: str) -> str:
    """
    Cleanup a text, dropping special characters and replacing whitespaces.
    """
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^\w\-_.]", "", text)
    return text


def read_config(config_root: str) -> Dict[str, List[dict]]:
    """
    Read all config JSON files from CSB.
    """
    plots_by_app: Dict[str, List[dict]] = {}

    if not os.path.isdir(config_root):
        print(f"Warning: Config root {config_root} does not exist.")
        return plots_by_app

    for root, _, files in os.walk(config_root):
        for f in files:
            if not f.lower().endswith(".json"):
                continue

            json_path = os.path.join(root, f)
            try:
                with open(json_path, "r", encoding="utf-8") as ff:
                    data = json.load(ff)
            except Exception as e:
                print(f"Failed to load {json_path}: {e}")
                continue

            linearity_plots = [
                p for p in data.get("plots", []) if p.get("type") == "linearity"
            ]

            app = os.path.basename(f).replace(".json", "")
            plots_by_app[app] = linearity_plots

    return plots_by_app


def generate_html(
    structured_plots: Dict[str, Dict[str, List[Tuple[str, str]]]], out_dir: str
) -> str:
    """Generate a clean, indented HTML gallery and write it to out_dir/index.html"""
    html_header = dedent(
        """\
        <!DOCTYPE html>
        <html lang='en'>
        <head>
        <meta charset='utf-8'>
        <title>Benchmark Comparison</title>
        <style>
            body { font-family: system-ui, -apple-system, sans-serif; margin: 30px; background: #fafafa; color: #333; }
            h1 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
            h2 { margin-top: 40px; color: #0056b3; }
            .plot-card { background: #fff; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
            img { max-width: 920px; height: auto; display: block; margin: 10px auto; }
            .exec-type { font-weight: bold; color: #555; margin-top: 15px; border-left: 4px solid #0056b3; padding-left: 10px; }
        </style>
        </head>
        <body>
        <h1>Benchmark Comparison</h1>
    """
    )

    cols_to_check = ["NATIVE", "CONTAINER"]
    html_body_lines = ["<table>", "  <tbody>"]

    for _, types in structured_plots.items():
        html_body_lines.append("    <tr>")

        others = []
        table_cols = {}
        for etype, cols in types.items():
            # Match if "NATIVE" is part of the execution_type string
            matched = False
            for target in cols_to_check:
                if target.upper() in etype.upper():
                    table_cols[target] = cols
                    matched = True
                    break
            if not matched:
                others.append(etype)

        # NATIVE column
        html_body_lines.append("      <td>")
        for title, rel_path in table_cols.get("NATIVE", []):
            html_body_lines[-1] += f"{title}<img src='{rel_path}'>"
        html_body_lines[-1] += "</td>"

        # CONTAINER column
        html_body_lines.append("      <td>")
        for title, rel_path in table_cols.get("CONTAINER", []):
            html_body_lines[-1] += f"{title}><img src='{rel_path}'>"
        html_body_lines[-1] += "</td>"

        # Others column (if needed)
        if others:
            html_body_lines.append("      <td>")
            for o_type in others:
                for title, rel_path in types[o_type]:
                    html_body_lines[-1] += f"{o_type}: {title}<img src='{rel_path}'>"
            html_body_lines[-1] += "</td>"

        html_body_lines.append("    </tr>")

    html_body_lines.append("  </tbody>")
    html_body_lines.append("</table>")

    html_footer = "</body>\n</html>"
    html_content = html_header + "\n".join(html_body_lines) + html_footer

    html_path = os.path.join(out_dir, "index.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nHTML with plots written to: {html_path}")
    return html_path


def plot_chart(
    params: PlotParams,
    df: pd.DataFrame,
    out_dir: str,
    out_prefix: str,
    palette: Dict[str, any],
    debug: bool = False,
) -> str:
    """
    Create a seaborn plot, saving it as PNG.
    """
    plt.figure(figsize=(12, 7), dpi=150)

    # Sanity checks
    for col in (params.x, params.y, params.hue):
        if col not in df.columns:
            print(f"Error: Column '{col}' not found in data.")
            plt.close()
            return ""

    ax = sns.lineplot(
        data=df,
        x=params.x,
        y=params.y,
        hue=params.hue,
        markers=params.hue,
        palette=palette,
        estimator="mean",
    )

    sns.scatterplot(
        data=df,
        x=params.x,
        y=params.y,
        hue=params.hue,
        markers=params.hue,
        palette=palette,
        legend=False,
    )

    if params.hue_lbl:
        title = params.hue_lbl
    else:
        title = params.hue

    ax.set_title(params.title)
    ax.set_xlabel(params.x_lbl or params.x)
    ax.set_ylabel(params.y_lbl or params.y)
    ax.set_ylim(0)
    ax.legend(title=title, bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    out_path = os.path.join(out_dir, f"{out_prefix}.png")
    plt.savefig(out_path)
    plt.close()

    if debug:
        print(f"Saved plot '{params.title}' to: {out_path}")

    return out_path


#
# Main
#
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate linearity plots from benchmark CSVs."
    )
    parser.add_argument(
        "csv_dirs", nargs="+", help="Directories that contain CSV files."
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug.")
    parser.add_argument(
        "--config-root", default="config", help="Root directory with JSON config files."
    )
    parser.add_argument(
        "--output-dir",
        default="plots",
        help="Directory where PNGs and index.html will be written.",
    )
    args = parser.parse_args()

    config_root = os.path.abspath(args.config_root)
    out_dir = os.path.abspath(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Collect CSV files
    csv = []
    for d in args.csv_dirs:
        for f in iglob(os.path.join(d, "**/*.csv"), recursive=True):
            new_csv = get_csv(f)
            if new_csv is not None:
                if args.debug:
                    print(f"Appending data from {f}")
                csv.append(new_csv)

    if not csv:
        sys.exit("No valid data loaded. Exiting.")

    df = pd.concat(csv, ignore_index=True)

    # Create a global palette for consistent kernel coloring
    kernels = sorted(df["kernel_version"].dropna().unique())
    global_palette = dict(zip(kernels, sns.color_palette("tab10", len(kernels))))

    # Load plots from JSON config
    plots_by_app = read_config(config_root)
    if not plots_by_app:
        sys.exit(f"No linearity plots found under {config_root}. Exiting.")

    # Filter by app using pandas boolean indexing (exactly as requested)
    structured_plots: Dict[str, Dict[str, List[Tuple[str, str]]]] = {}
    counter: Dict[Tuple[str, str], int] = {}

    for app in df["app"].dropna().unique():
        filter_app = df["app"] == app
        if app not in plots_by_app:
            continue

        exec_types = df["execution_type"].dropna().unique()
        if args.debug:
            print(f"Processing app: {app} ({len(exec_types)} execution types)")

        for etype in exec_types:
            filter_et = df["execution_type"] == etype

            df_filtered = df[filter_app & filter_et]

            if df_filtered.empty:
                continue

            plot_defs = plots_by_app[app]

            # Convert type on just "NATIVE" / "CONTAINER" without enum name
            _, _, etype_short = etype.partition(".")

            for plot_def in plot_defs:
                x, y = plot_def.get("x"), plot_def.get("y")
                if (
                    not x
                    or not y
                    or x not in df_filtered.columns
                    or y not in df_filtered.columns
                ):
                    continue

                params = PlotParams(
                    x=x,
                    y=y,
                    hue="kernel_version",
                    x_lbl=plot_def.get("x_lbl", x),
                    y_lbl=plot_def.get("y_lbl", y),
                    title=f"{app}: {etype_short}: {plot_def.get('title', f'{x} vs {y}')}",
                    hue_lbl="Kernel",
                )
                key = (app, etype)
                counter[key] = counter.get(key, 0) + 1
                prefix = f"{clear_string(app)}-{clear_string(etype)}-{counter[key]:03d}"

                out_path = plot_chart(
                    params, df_filtered, out_dir, prefix, global_palette, args.debug
                )

                if not out_path:
                    continue

                rel_path = os.path.relpath(out_path, out_dir)
                if app not in structured_plots:
                    structured_plots[app] = {}

                if etype not in structured_plots[app]:
                    structured_plots[app][etype] = []

                structured_plots[app][etype].append((params.title, rel_path))

    # Generate HTML gallery
    if structured_plots:
        generate_html(structured_plots, out_dir)

    if args.debug:
        print(f"\nAll plots written to: {out_dir}")


if __name__ == "__main__":
    main()
