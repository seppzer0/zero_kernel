import os
import stat
import glob
import shutil
from pathlib import Path
from typing import Optional

from builder.tools import commands as ccmd
from builder.configs import DirectoryConfig as dcfg


def remove(elements: str | Path | list[Path | str]) -> None:
    """Remove files and directories as a Pythonic alternative to 'rm -rf'.

    Here, all Path() objects will have to be converted into str.
    Because of such specific as directories starting with a "." (e.g., .github).

    :param str/Path/list[Path] elements: Files and/or directories to remove.
    """
    # if a given argument is a string --> convert it into a one-element list
    if isinstance(elements, str) or isinstance(elements, Path):
        elements = [str(elements)]
    for e in elements:
        # force convert into str
        e = str(e)
        # a simple list-through removal
        if "*" not in e:
            if os.path.isdir(e):
                shutil.rmtree(e, onerror=on_rm_error)
            elif os.path.isfile(e):
                os.remove(e)
        # a recursive "glob" removal
        else:
            for fn in glob.glob(e):
                remove(fn)


def on_rm_error(func, path: str, exc_info):
    """For Windows system to remove a .git folder.
    
    :param func: Function to be used along with.
    :param Path path: Path that is being removed.
    :exc_info param: Misc info.
    """
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def git(directory: Path | str) -> None:
    """Clean up a git directory.

    :param Path/str directory: Path to the directory.
    """
    goback = Path.cwd()
    os.chdir(directory)
    ccmd.launch("git clean -fdx")
    ccmd.launch("git reset --hard HEAD")
    os.chdir(goback)


def root(extra: Optional[list[str]] = []) -> None:
    """Fully clean the root directory.

    :param Optional[list[str]]=[] extra: Extra elements to be removed.
    """
    trsh = [
        dcfg.kernel,
        dcfg.assets,
        dcfg.bundle,
        "android_*",
        "*_kernel_*",
        "clang*",
        "AnyKernel3",
        "rtl8812au",
        "source",
        "localversion",
        "KernelSU",
        "multi-build",
        ".coverage",
        ".vscode",
        ".pytest_cache"
    ]
    # add extra elements to clean up from root directory
    if extra:
        for e in extra:
            trsh.append(dcfg.root / e)
    # clean
    remove(trsh)
    [remove(p) for p in Path(".").rglob("__pycache__")]
