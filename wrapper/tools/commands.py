import os
import subprocess
from typing import Union

import wrapper.tools.messages as msg


def launch(cmd: str, loglvl: str = os.getenv("LOGLEVEL", "normal"), get_output: bool = False) -> Union[str, None]:
    """
    A custom subprocess wrapper to launch commands.

    :param str cmd: A command to launch.
    :param str loglvl: Log level.
    """
    # determine stdout and check some of the cases
    sstdout = subprocess.DEVNULL if loglvl == "quiet" else os.getenv("OSTREAM", None)
    if get_output is True:
        sstdout = subprocess.PIPE
    # if output stream is a file -- open it
    if isinstance(sstdout, str):
        sstdout = open(sstdout, "a")
    if loglvl == "quiet" and os.getenv("OSTREAM"):
        msg.error("Cannot run 'quiet' build with file logging")
    elif loglvl == "verbose":
        print(f"[cmd] {cmd}")
    # avoid using shell
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=sstdout, stderr=subprocess.STDOUT)
        # return only output if required
        if get_output is True:
            return result.stdout.decode('utf-8').splitlines()[0]
    except Exception:
        msg.error(f"Error executing command: {cmd}")
    # if output stream is a file -- close it
    if isinstance(sstdout, str):
        sstdout.close()
