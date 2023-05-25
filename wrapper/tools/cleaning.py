import os
import glob
import shutil
from typing import List, Union
import commands as ccmd


def remove(elements: Union[str, List[str]], allow_errors: bool = False):
    """An ultimate alternative to 'rm -rf'.

    :param elements: Files and/or directories to remove.
    :param bool allow_errors: Don't exit on errors.
    :type elements: str or List[str]
    """
    # if a given argument is a string --> convert it into a one-element list
    if isinstance(elements, str):
        elements = [elements]
    for e in elements:
        # a simple list-through removal
        if "*" not in e:
            if os.path.isdir(e):
                shutil.rmtree(e, ignore_errors=allow_errors)
            elif os.path.isfile(e):
                os.remove(e)
        # a recursive "glob" removal
        else:
            for fn in glob.glob(e):
                remove(fn)


def git(directory: str) -> None:
    """Clean up a git directory.

    :param str directory: Path to the directory.
    """
    goback = os.getcwd()
    os.chdir(directory)
    ccmd.launch("git clean -fdx")
    ccmd.launch("git reset --hard HEAD")
    os.chdir(goback)


def root(extra: List[str] = []) -> None:
    """Fully clean the root directory.

    NOTE: .vscode is not cleaned, __pycache__ --> via py3clean

    :param list extra: Extra elements to be removed.
    """
    trsh = ["android_*",
            "clang*",
            "AnyKernel3",
            "rtl8812au",
            "source",
            "kernel",
            "localversion",
            "assets",
            "release-slim",
            "conanfile.py"]
    # add extra elements to clean up from root directory
    if extra:
        for e in extra:
            trsh.append(e)
    # clean
    remove(trsh, allow_errors=True)
    ccmd.launch("py3clean .")
