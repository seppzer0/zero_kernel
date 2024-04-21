import os
import shutil
import argparse
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env",
        choices=("docker", "podman", "local"),
        default="docker"
    )
    return parser.parse_args()


def rmove(src: Path, dst: Path) -> None:
    """Recursively move files from one directory to another.

    :param Path src: Source path.
    :param Path dst: Destination path.
    """
    # for a directory (it's contents)
    if src.is_dir():
        if not dst.is_dir():
            os.mkdir(dst)
        contents = os.listdir(src)
        for e in contents:
            # do not copy restricted files
            if e != src:
                src_e = src / e
                dst_e = dst / e
                shutil.move(src_e, dst_e)
    # for a single file
    elif src.is_file():
        shutil.move(src, dst)


def main(args: argparse.Namespace) -> None:
    """Run multi build."""
    rootpath = Path(__file__).absolute().parents[1]
    argsets = (
        {
            "command": "bundle",
            "rom": "los",
            "codename": "dumpling",
            "lkv": "4.4",
            "ksu": False
        },
        {
            "command": "kernel",
            "rom": "los",
            "codename": "dumpling",
            "lkv": "4.4",
            "ksu": True
        },
        {
            "command": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "lkv": "4.4",
            "ksu": False
        },
        {
            "command": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "lkv": "4.4",
            "ksu": True
        },
        {
            "command": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "lkv": "4.14",
            "ksu": False
        },
        {
            "command": "assets",
            "rom": "los",
            "codename": "cheeseburger",
            "ksu": True
        },
    )
    os.chdir(rootpath)
    dir_shared = rootpath / "multi-build"
    shutil.rmtree(dir_shared, ignore_errors=True)
    os.mkdir(dir_shared)
    for count, argset in enumerate(argsets, 1):
        # define some of the values individually
        benv = f"--build-env {args.env}"
        base = f'--base {argset["rom"]}'
        codename = f'--codename {argset["codename"]}'
        lkv = f'--lkv {argset["lkv"]}' if argset["command"] in ("kernel", "bundle") else ""
        ksu = "--ksu" if argset["ksu"] else ""
        size = "--package-type slim" if argset["command"] == "bundle" else ""
        extra = "--chroot minimal --rom-only --clean" if argset["command"] == "assets" else ""
        # if the build is last, make it automatically remove the Docker/Podman image from runner
        clean_image = "--clean-image" if count == len(argsets) and args.env in ("docker", "podman") else ""
        # form and launch the command
        cmd = f"python3 builder {argset['command']} {benv} {base} {codename} {lkv} {size} {ksu} {clean_image} {extra}"
        print(f"[CMD]: {cmd}")
        subprocess.run(cmd.strip(), shell=True, check=True)
        # copy artifacts into the shared directory
        out = ""
        match argset["command"]:
            case "bundle":
                out = "bundle"
            case "kernel":
                out = "kernel"
            case "assets":
                out = "assets"
        # convert into full path
        out = Path(rootpath, out)
        rmove(out, dir_shared)


if __name__ == "__main__":
    main(parse_args())
