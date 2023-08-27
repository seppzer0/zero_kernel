import os
import shutil
import subprocess
from pathlib import Path
from typing import List


def ucopy(src: Path, dst: Path, exceptions: List[str] = []) -> None:
    """A universal method to copy files into desired destinations.

    :param src: Source path.
    :param dst: Destination path.
    :param exceptions: Elements that will not be removed.
    """
    # for a directory (it's contents)
    if src.is_dir():
        if not dst.is_dir():
            os.mkdir(dst)
        contents = os.listdir(src)
        for e in contents:
            # do not copy restricted files
            if e not in exceptions and e != src:
                src_e = Path(src, e)
                dst_e = Path(dst, e)
                if src_e.is_dir():
                    shutil.copytree(src_e, dst_e)
                elif src_e.is_file():
                    shutil.copy(src_e, dst_e)
    # for a single file
    elif src.is_file():
        shutil.copy(src, dst)


# launch the builds
apath = Path(Path(__file__).absolute().parents[1])
# those with "bundle" module usage are primarily tested builds
argsets = (
    {
        "module": "bundle",
        "rom": "los",
        "codename": "dumpling",
        "ksu": "false",
        "size": "slim"
    },
    #{
    #    "module": "bundle",
    #    "rom": "aospa",
    #    "codename": "dumpling",
    #    "ksu": "false",
    #    "size": "slim"
    #},
    {
        "module": "kernel",
        "rom": "los",
        "codename": "dumpling",
        "ksu": "true"
    },
    #{
    #    "module": "kernel",
    #    "rom": "aospa",
    #    "codename": "dumpling",
    #    "ksu": "true"
    #},
    {
        "module": "assets",
        "rom": "los",
        "codename": "cheeseburger",
        "ksu": "true"
    },
    #{
    #    "module": "assets",
    #    "rom": "aospa",
    #    "codename": "cheeseburger",
    #    "ksu": "true"
    #}
)
os.chdir(apath)
dir_shared = "multi_slim"
shutil.rmtree(dir_shared, ignore_errors=True)
for count, argset in enumerate(argsets, 1):
    # create artifact holder directory
    if dir_shared not in os.listdir():
        os.mkdir(dir_shared)
    # extract individual values
    module = argset["module"]
    rom = argset["rom"]
    codename = argset["codename"]
    ksu = "--ksu" if argset["ksu"] == "true" else ""
    size = argset["size"] if argset["module"] == "bundle" else ""
    extra = "minimal --rom_only --clean" if argset["module"] == "assets" else ""
    # if the build is last, make it automatically remove the Docker image from runner
    clean = "--clean-image" if count == len(argsets) else ""
    # form and launch the command
    cmd = f"python3 wrapper {module} docker {rom} {codename} {size} {ksu} {clean} {extra}"
    print(f"[CMD]: {cmd}")
    subprocess.run(cmd.strip(), shell=True, check=True)
    # copy artifacts into the shared directory
    out = ""
    if argset["module"] == "bundle":
        out = f"release-{size}"
    elif argset["module"] == "kernel":
        out = "kernel"
    elif argset["module"] == "assets":
        out = "assets"
    ucopy(Path(out), Path(dir_shared))
