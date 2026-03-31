import os
import signal
import subprocess
from utils.logger import bm_log, LogType
from typing import Optional
from bm_utils import ensure_exists

class BackgroundProcess:
    TIMEOUT_SEC = 5
    Env = {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}

    def __init__(self, name:str, out_dir: str, cmds: list[str], wdir: Optional[str] = None, ofile_name: Optional[str] = None):
        assert len(cmds) > 1, "expected at least the process name"
        self.name = name
        self.efile_name = os.path.join(out_dir, f"{self.name}.err")
        if ofile_name is None:
            self.ofile_name = os.path.join(out_dir, f"{self.name}.log")
        else:
            self.ofile_name = os.path.join(out_dir, ofile_name)
        self.cmds = cmds
        self.wdir = out_dir if wdir is None else wdir
        self.process : Optional[subprocess.Popen] = None
        # ensure process exist
        ensure_exists(self.name)

    def start(self):
        assert self.process == None, "it seems, it has already been started!"
        self.ofile = open(self.ofile_name, "w")
        self.efile = open(self.efile_name, "w")
        self.process = subprocess.Popen(
            self.cmds,
            stdout=self.ofile,
            stderr=self.efile,
            env=self.Env,
            preexec_fn=os.setpgrp,
            cwd=self.wdir
        )
        cmd_str =" ".join(self.cmds)
        bm_log(f"Running {cmd_str}")

    def stop(self):
        bm_log(f"Sending cancel signal to {self.name}")
        self.process.send_signal(signal.SIGINT)
        try:
            self.process.wait()
            if self.process.returncode != 0:
                bm_log(f"{self.name} exited with {self.process.returncode}.", LogType.ERROR)
        except subprocess.TimeoutExpired:
            bm_log(f"{self.name} timeout on exit!", LogType.ERROR)
        self.ofile.close()
        self.efile.close()

    def read_output(self):
        try:
            with open(self.ofile_name, "r") as file:
                return file.read()
        except Exception as e:
            bm_log(f"Failed to read {self.ofile_name} {e}", LogType.ERROR)
            return ""
