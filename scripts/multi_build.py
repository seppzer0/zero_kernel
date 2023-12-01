import os
import shutil
import argparse
import subprocess
from pathlib import Path


def parse_args() -> None:
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env",
        choices=("docker", "podman", "local"),
        default="docker"
    )
    return parser.parse_args()


def rmove(src: Path, dst: Path) -> None:
    """Recusrively move files from one directory to another.

    :param src: Source path.
    :param dst: Destination path.
    """
    # for a directory (it's contents)
    if src.is_dir():
        if not dst.is_dir():
            os.mkdir(dst)
        contents = os.listdir(src)
        for e in contents:
            # do not copy restricted files
            if e != src:
                src_e = Path(src, e)
                dst_e = Path(dst, e)
                shutil.move(src_e, dst_e)
    # for a single file
    elif src.is_file():
        shutil.move(src, dst)


def main(args: argparse.Namespace) -> None:
    """Run multi build."""
    apath = Path(Path(__file__).absolute().parents[1])
    argsets = (
        {
            "module": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "lkv": "4.4",
            "ksu": False
        },
        {
            "module": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "lkv": "4.4",
            "ksu": True
        },
        {
            "module": "kernel",
            "rom": "pa",
            "codename": "dumpling",
            "lkv": "4.14",
            "ksu": True
        },
        {
            "module": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "lkv": "4.14",
            "ksu": True
        },
        {
            "module": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "lkv": "4.14",
            "ksu": False
        },
        {
            "module": "assets",
            "rom": "los",
            "codename": "cheeseburger",
            "ksu": True
        },
        {
            "module": "assets",
            "rom": "pa",
            "codename": "cheeseburger",
            "ksu": True
        },
    )
    os.chdir(apath)
    dir_shared = "multi-build"
    shutil.rmtree(dir_shared, ignore_errors=True)
    for count, argset in enumerate(argsets, 1):
        # create artifact holder directory
        if dir_shared not in os.listdir():
            os.mkdir(dir_shared)
        # define values individually
        module = argset["module"]
        buildenv = f"--buildenv {args.env}"
        base = f'--base {argset["rom"]}'
        codename = f'--codename {argset["codename"]}'
        lkv = f'--lkv {argset["lkv"]}' if argset["module"] in ("kernel", "bundle") else ""
        ksu = "--ksu" if argset["ksu"] else ""
        size = f'--package-type {argset["size"]}' if argset["module"] == "bundle" else ""
        extra = "minimal --rom-only --clean" if argset["module"] == "assets" else ""
        # if the build is last, make it automatically remove the Docker/Podman image from runner
        clean = "--clean-image" if count == len(argsets) and args.env in ("docker", "podman") else ""
        # form and launch the command
        cmd = f"python3 wrapper {module} {buildenv} {base} {codename} {lkv} {size} {ksu} {clean} {extra}"
        print(f"[CMD]: {cmd}")
        subprocess.run(cmd.strip(), shell=True, check=True)
        # copy artifacts into the shared directory
        out = ""
        match argset["module"]:
            case "bundle":
                out = "bundle"
            case "kernel":
                out = "kernel"
            case "assets":
                out = "assets"
        rmove(Path(out), Path(dir_shared))


if __name__ == "__main__":
    # launch the builds
    main(parse_args())
