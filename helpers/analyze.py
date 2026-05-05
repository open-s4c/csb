import os
import pandas as pd

# collect all csvs in the given folder
def find_csvs(folder_path:str):
    files = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            file_path = os.path.join(folder_path, file_name)
            files.append(file_path)
    return files

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
        grouped = df.groupby(['algo_name', 'execution_type', 'kernel', 'num_threads'])
        for key, g in grouped:
            algo_name, execution_type, kernel, num_threads = key

            avg_per_container = g.groupby('container_cnt')['throughput_min'].mean()
            min_container     = avg_per_container.index.min()
            avg_min_throughput = avg_per_container[min_container]
            linearity_per_count = avg_per_container / avg_min_throughput

            dropped = linearity_per_count[(linearity_per_count < (1 - tolerance))]
            if dropped.empty:
                checkmark = "✔"
                drop_note = ""
            else:
                checkmark = "✘"
                drop_note = str(dropped.index.min())

            results.append({
                'Benchmark': algo_name,
                'Execution Unit': execution_type,
                'Kernel': kernel,
                'Number of Threads': num_threads,
                'linear': checkmark,
                'Drops at': drop_note
            })

        return results
    except Exception as e:
        print(f"{e} on {file}")
        return results

if __name__ == "__main__":
    folder = "/home/lilith/workspace/csb/amd-results"
    files = find_csvs(folder)
    all = []
    for f in files:
        res = process(f)
        all.extend(res)

    final_df = pd.DataFrame(all)
    md_table = final_df.to_markdown(index=False)
    with open("results.md", "w") as f:
         f.write(md_table)
