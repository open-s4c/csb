# This class is responsible of building builtin
# CSB targets/benchmarks

from bm_utils import get_project_dir
from benchkit.shell.shell import shell_out
import os
from utils.logger import bm_log, LogType
class Builder:
    project_dir:str ="."
    build_dir:str   ="build"

    def __init__(self):
        self.project_dir = get_project_dir()
        self.build_dir = os.path.join(self.project_dir, self.build_dir)

    def __run_cmake_config(self):
        cmd = f"cmake -DCMAKE_BUILD_TYPE=Release -S{self.project_dir} -B{self.build_dir}"
        shell_out(
            cmd,
            output_is_log=False,
            print_file_shell_cmd=False
        )

    def __get_targets(self) -> set[str]:
        self.__run_cmake_config()
        cmd = f"cmake --build {self.build_dir} --target help"
        output = shell_out(cmd,
                           print_shell_cmd=False,
                           print_output=False,
                           print_file_shell_cmd=False)
        try:
            # Split output by lines and remove the first line and '... ' from each target
            lines = output.splitlines()
            # Skip the first line, and strip the '... ' from each subsequent line, adding them to a set (hashset)
            targets = {line.strip()[4:] for line in lines[1:] if line.strip().startswith('...')}
            return targets
        except:
            bm_log("Failed to parse list of targets from cmake", LogType.ERROR)
            return {}

    def target_exists(self, target: str) -> bool:
        targets = self.__get_targets()
        return target in targets


