import os
import subprocess
from typing import Optional, Literal
from subprocess import CompletedProcess

from builder.tools import messages as msg


def launch(
        cmd: str,
        get_output: Optional[bool] = False,
        loglvl: Optional[Literal["normal", "quiet"]] = "normal"
    ) -> str | CompletedProcess | None:
    """Custom subprocess wrapper to launch commands.

    :param str cmd: Command to launch.
    :param Optional[bool]=False get_output: Switch to get the piped output of the command.
    :param str loglvl: Log level.
    :return: Result of command launch.
    :rtype: str | CompletedProcess | None
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

    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=cstdout, stderr=subprocess.STDOUT)

        # return only output if required
        if get_output is True:
            return result.stdout.decode("utf-8").rstrip()
        else:
            return result

    except Exception as e:
        msg.error(f"Error executing command: {cmd} -> {e}")
