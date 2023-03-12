import os
import sys
import subprocess


def launch(cmd, loglvl=os.getenv("LOGLEVEL", "normal")):
    """A custom subprocess wrapper to launch commands."""
    if loglvl == "verbose":
        print(f"[cmd] {cmd}")
    if loglvl == "quiet":
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, check=False)
    else:
        subprocess.run(cmd, shell=True, check=False)


# generate reports in multiple file formats
formats = ["json", "html"]
apath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "wrapper")
for ft in formats:
    launch(f"python3 -m bandit -r -f {ft} {apath} -o report.{ft}", "verbose")
