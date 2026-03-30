import os
import signal
import subprocess
from utils.logger import bm_log, LogType
from typing import Optional
from bm_utils import ensure_exists

class BackgroundProcess:
    TIMEOUT_SEC = 5
    def __init__(self, out_dir: str, cmds: list[str], wdir: str):
        assert len(cmds) > 1, "expected at least the process name"
        self.name = cmds[0]
        self.efile = os.path.join(out_dir, f"{out_dir}.err")
        self.ofile = os.path.join(out_dir, f"{out_dir}.log")
        self.cmds = cmds
        self.process : Optional[subprocess.Popen] = None
        # ensure process exist
        ensure_exists(self.name)

    def start(self):
        assert self.process == None, "it seems, it has already been started!"
        self.process = subprocess.Popen(
            self.cmds,
            stdout=self.ofile,
            stderr=self.efile,
            preexec_fn=os.setpgrp
        )

    def stop(self):
        bm_log(f"Sending cancel signal to {self.name}")
        self.process.send_signal(signal.SIGINT)
        try:
            self.process.wait(self.TIMEOUT_SEC)
            if self.process.returncode != 0:
                bm_log(f"{self.name} exited with {self.process.returncode}.", LogType.ERROR)
        except subprocess.TimeoutExpired:
            bm_log(f"{self.name} timeout on exit!", LogType.ERROR)
