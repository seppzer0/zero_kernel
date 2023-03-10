import os
import sys
import subprocess


def launch(cmd, loglvl=os.getenv("LOGLEVEL", "normal")):
    """A custom subprocess wrapper to launch commands."""
    if loglvl == "verbose":
        print(f"[cmd] {cmd}")
    if loglvl == "quiet":
        rc = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL).returncode
    else:
        rc = subprocess.run(cmd, shell=True).returncode
    # in case of an error -> exit with message
    if rc != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(1)


# generate reports in multiple file formats
formats = ["json", "html"]
apath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "wrapper")
for ft in formats:
    launch(f"python3 -m bandit -r -f {ft} {apath} -o report.{ft}", "verbose")
