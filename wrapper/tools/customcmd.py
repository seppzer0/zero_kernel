import os
import sys
import subprocess
import messagedecorator as msg


def launch(cmd, loglvl=os.getenv("LOGLEVEL", "normal")):
    """A custom subprocess wrapper to launch commands."""
    # determine stdout and check some of the cases
    sstdout = subprocess.DEVNULL if loglvl == "quiet" else os.getenv("OSTREAM", None)
    # if output stream is a file -- open it
    if isinstance(sstdout, str):
        sstdout = open(sstdout, "a")
    if loglvl == "quiet" and os.getenv("OSTREAM"):
        msg.error("Cannot run 'quiet' build with file logging")
    elif loglvl == "verbose":
        print(f"[cmd] {cmd}")
    rc = subprocess.run(cmd, shell=True, stdout=sstdout, stderr=subprocess.STDOUT).returncode
    # if output stream is a file -- close it
    if isinstance(sstdout, str):
        sstdout.close()
    # in case of an error -> exit with message
    if rc != 0:
        msg.error(f"Error executing command: {cmd}")
