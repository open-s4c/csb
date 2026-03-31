import os
import signal
import subprocess
from utils.logger import bm_log, LogType
from typing import Optional
from bm_utils import ensure_exists

class BackgroundProcess:
    TIMEOUT_SEC = 5
    def __init__(self, name:str, out_dir: str, cmds: list[str], wdir: Optional[str] = None):
        assert len(cmds) > 1, "expected at least the process name"
        self.name = name
        self.efile = os.path.join(out_dir, f"{self.name}.err")
        self.ofile = os.path.join(out_dir, f"{self.name}.log")
        self.cmds = cmds
        self.wdir = out_dir if wdir is None else wdir
        self.process : Optional[subprocess.Popen] = None
        # ensure process exist
        ensure_exists(self.name)

    def start(self):
        assert self.process == None, "it seems, it has already been started!"
        #self.ofile = open(self.ofile, "w")
        #self.efile = open(self.efile, "w")
        self.process = subprocess.Popen(
            self.cmds,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
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
        #self.ofile.close()
        #self.efile.close()
