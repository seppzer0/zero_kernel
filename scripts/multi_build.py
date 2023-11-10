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


def ucopy(src: Path, dst: Path) -> None:
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
            if e != src:
                src_e = Path(src, e)
                dst_e = Path(dst, e)
                if src_e.is_dir():
                    shutil.copytree(src_e, dst_e)
                elif src_e.is_file():
                    shutil.copy(src_e, dst_e)
    # for a single file
    elif src.is_file():
        shutil.copy(src, dst)


def main(args: argparse.Namespace) -> None:
    """Run multi build."""
    apath = Path(Path(__file__).absolute().parents[1])
    argsets = (
        {
            "module": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "ksu": "false"
        },
        {
            "module": "kernel",
            "rom": "x",
            "codename": "dumpling",
            "ksu": "true"
        },
        {
            "module": "assets",
            "rom": "los",
            "codename": "cheeseburger",
            "ksu": "true"
        },
        {
            "module": "assets",
            "rom": "pa",
            "codename": "cheeseburger",
            "ksu": "true"
        },
    )
    os.chdir(apath)
    dir_shared = "multi-build"
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
        extra = "minimal --rom-only --clean" if argset["module"] == "assets" else ""
        # if the build is last, make it automatically remove the Docker/Podman image from runner
        clean = "--clean-image" if count == len(argsets) and args.env in ("docker", "podman") else ""
        # form and launch the command
        cmd = f"python3 wrapper {module} {args.env} {rom} {codename} {size} {ksu} {clean} {extra}"
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
        ucopy(Path(out), Path(dir_shared))


if __name__ == "__main__":
    # launch the builds
    main(parse_args())
