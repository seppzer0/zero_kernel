import os
import subprocess
from . import messagedecorator as msg


def launch(cmd, loglvl=os.getenv("LOGLEVEL")):
    """A custom subprocess wrapper to launch commands."""
    if loglvl == "verbose":
        print(f"[cmd] {cmd}")
    if loglvl == "quiet":
        rc = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL).returncode
    else:
        rc = subprocess.run(cmd, shell=True).returncode
    # in case of an error -> exit with message
    if rc != 0:
        msg.error(f"Error executing command: {cmd}")
