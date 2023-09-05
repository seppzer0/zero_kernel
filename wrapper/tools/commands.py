import os
import subprocess
from typing import Union

import tools.messages as msg


def launch(
        cmd: str,
        get_output: bool = False,
        loglvl: str = os.getenv("LOGLEVEL", "normal")
    ) -> Union[str, None]:
    """
    A custom subprocess wrapper to launch commands.

    :param cmd: A command to launch.
    :param loglvl: Log level.
    :param get_output: A switch to get the piped output of the command.
    """
    # determine stdout and check some of the cases
    cstdout = subprocess.DEVNULL if loglvl == "quiet" else os.getenv("OSTREAM", None)
    if get_output is True:
        cstdout = subprocess.PIPE
    # if output stream is a file -- open it
    if isinstance(cstdout, str):
        cstdout = open(cstdout, "a")
    if loglvl == "quiet" and os.getenv("OSTREAM"):
        msg.error("Cannot run 'quiet' build with file logging")
    elif loglvl == "verbose":
        print(f"[cmd] {cmd}")
    # avoid using shell
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=cstdout, stderr=subprocess.STDOUT)
        # return only output if required
        if get_output is True:
            return result.stdout.decode('utf-8').splitlines()[0]
    except Exception:
        msg.error(f"Error executing command: {cmd}")
    # if output stream is a file -- close it
    if isinstance(cstdout, str):
        cstdout.close()
