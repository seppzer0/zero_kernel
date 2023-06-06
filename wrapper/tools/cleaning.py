import os
import shutil
from pathlib import Path
from typing import List, Union

import wrapper.tools.commands as ccmd


def remove(elements: Union[os.PathLike, List[os.PathLike]], allow_errors: bool = False) -> None:
    """An ultimate alternative to 'rm -rf'.

    Here, all Path() objects will have to be converted into str.
    Because of such specific as directories starting with a "." (e.g., .github).

    :param elements: Files and/or directories to remove.
    :param bool allow_errors: Don't exit on errors.
    :type elements: path or list[path]
    """
    # if a given argument is a string --> convert it into a one-element list
    if isinstance(elements, str) or isinstance(elements, os.PathLike):
        elements = [str(elements)]
    for e in elements:
        # force convert into str
        e = str(e)
        # a simple list-through removal
        if "*" not in e:
            if os.path.isdir(e):
                shutil.rmtree(e, ignore_errors=allow_errors)
            elif os.path.isfile(e):
                os.remove(e)
        # a recursive "glob" removal
        else:
            for fn in Path(e).glob("*"):
                remove(fn)


def git(directory: os.PathLike) -> None:
    """Clean up a git directory.

    :param path directory: Path to the directory.
    """
    goback = Path.cwd()
    os.chdir(directory)
    ccmd.launch("git clean -fdx")
    ccmd.launch("git reset --hard HEAD")
    os.chdir(goback)


def root(extra: List[str] = []) -> None:
    """Fully clean the root directory.

    .vscode is not cleaned, __pycache__ --> via py3clean

    :param list extra: Extra elements to be removed.
    """
    trsh = [
        "android_*",
        "clang*",
        "AnyKernel3",
        "rtl8812au",
        "source",
        "kernel",
        "localversion",
        "assets",
        "release-slim",
        "conanfile.py"
    ]
    # add extra elements to clean up from root directory
    if extra:
        for e in extra:
            trsh.append(Path(os.getenv("ROOTPATH"), e))
    # clean
    remove(trsh, allow_errors=True)
    ccmd.launch("py3clean .")
