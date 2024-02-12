import os
import sys
import json
import argparse
import platform
from pathlib import Path

import tools.cleaning as cm
import tools.messages as msg
import tools.commands as ccmd

from models.bundle_creator import BundleCreator
from models.kernel_builder import KernelBuilder
from models.assets_collector import AssetsCollector

from engines.docker_engine import DockerEngine
from engines.podman_engine import PodmanEngine

from configs import Config as cfg


def parse_args() -> argparse.Namespace:
    """Parse the script arguments."""
    # show the 'help' message if no arguments supplied
    args = None if sys.argv[1:] else ["-h"]
    # parser and subparsers
    parser_parent = argparse.ArgumentParser(description="A custom wrapper for the zero kernel.")
    subparsers = parser_parent.add_subparsers(dest="command")
    parser_kernel = subparsers.add_parser("kernel", help="build the kernel")
    parser_assets = subparsers.add_parser("assets", help="collect assets")
    parser_bundle = subparsers.add_parser("bundle", help="build the kernel + collect assets")
    # add a single argument for the main parser
    parser_parent.add_argument(
        "--clean",
        dest="clean_root",
        action="store_true",
        help="clean the root directory"
    )
    # common argument attributes for subparsers
    help_base = "select a kernel base for the build"
    help_codename = "select device codename"
    help_benv = "select build environment"
    help_clean = "remove Docker/Podman image from the host machine after build"
    help_loglvl = "select log level"
    choices_benv = ("local", "docker", "podman")
    choices_loglvl = ("normal", "verbose", "quiet")
    choices_base = ("los", "pa", "x", "aosp")
    help_logfile = "save logs to a file"
    help_ksu = "add KernelSU support"
    help_lkv = "select Linux Kernel Version"
    default_loglvl = "normal"
    # kernel
    parser_kernel.add_argument(
        "--build-env",
        dest="benv",
        required=True,
        choices=choices_benv,
        help=help_benv,
    )
    parser_kernel.add_argument(
        "--base",
        required=True,
        help=help_base,
        choices=choices_base
    )
    parser_kernel.add_argument(
        "--codename",
        required=True,
        help=help_codename
    )
    parser_kernel.add_argument(
        "--lkv",
        required=True,
        help=help_lkv
    )
    parser_kernel.add_argument(
        "-c", "--clean",
        dest="clean_kernel",
        action="store_true",
        help="don't build anything, just clean the environment"
    )
    parser_kernel.add_argument(
        "--clean-image",
        action="store_true",
        dest="clean_image",
        help=help_clean
    )
    parser_kernel.add_argument(
        "--log-level",
        dest="loglvl",
        choices=choices_loglvl,
        default=default_loglvl,
        help=help_loglvl
    )
    parser_kernel.add_argument(
        "-o", "--output",
        dest="outlog",
        help=help_logfile
    )
    parser_kernel.add_argument(
        "--ksu",
        action="store_true",
        dest="ksu",
        help=help_ksu
    )
    # assets
    parser_assets.add_argument(
        "--build-env",
        dest="benv",
        required=True,
        choices=choices_benv,
        help=help_benv
    )
    parser_assets.add_argument(
        "--base",
        required=True,
        help=help_base,
        choices=choices_base
    )
    parser_assets.add_argument(
        "--codename",
        required=True,
        help=help_codename
    )
    parser_assets.add_argument(
        "--chroot",
        required=True,
        choices=("full", "minimal"),
        help="select Kali chroot type"
    )
    parser_assets.add_argument(
        "--rom-only",
        dest="rom_only",
        action="store_true",
        help="download only the ROM as an asset"
    )
    parser_assets.add_argument(
        "--clean-image",
        action="store_true",
        dest="clean_image",
        help=help_clean
    )
    parser_assets.add_argument(
        "--clean",
        dest="clean_assets",
        action="store_true",
        help="autoclean 'assets' folder if it exists"
    )
    parser_assets.add_argument(
        "--log-level",
        dest="loglvl",
        choices=choices_loglvl,
        default=default_loglvl,
        help=help_loglvl
    )
    parser_assets.add_argument(
        "-o", "--output",
        dest="outlog",
        help=help_logfile
    )
    parser_assets.add_argument(
        "--ksu",
        action="store_true",
        dest="ksu",
        help=help_ksu
    )
    # bundle
    parser_bundle.add_argument(
        "--build-env",
        dest="benv",
        required=True,
        choices=choices_benv,
        help=help_benv
    )
    parser_bundle.add_argument(
        "--base",
        required=True,
        help=help_base,
        choices=choices_base
    )
    parser_bundle.add_argument(
        "--codename",
        required=True,
        help=help_codename
    )
    parser_bundle.add_argument(
        "--lkv",
        required=True,
        help=help_lkv
    )
    parser_bundle.add_argument(
        "--package-type",
        required=True,
        dest="package_type",
        choices=("conan", "slim", "full"),
        help="select package type of the bundle"
    )
    parser_bundle.add_argument(
        "--conan-upload",
        action="store_true",
        dest="conan_upload",
        help="upload Conan packages to remote"
    )
    parser_bundle.add_argument(
        "--clean-image",
        action="store_true",
        dest="clean_image",
        help=help_clean
    )
    parser_bundle.add_argument(
        "--log-level",
        dest="loglvl",
        choices=choices_loglvl,
        default=default_loglvl,
        help=help_loglvl
    )
    parser_bundle.add_argument(
        "-o", "--output",
        dest="outlog",
        help=help_logfile
    )
    parser_bundle.add_argument(
        "--ksu",
        action="store_true",
        dest="ksu",
        help=help_ksu
    )
    return parser_parent.parse_args(args)


def validate_settings(config: dict) -> None:
    """Run settings validations.
    
    :param config: A dictionary containing app arguments.
    """
    # detect OS family
    if config.get("benv") == "local":
        if not platform.system() == "Linux":
            msg.error("Can't build kernel on a non-Linux machine.")
        else:
            # check that it is Debian-based
            try:
                ccmd.launch("apt --version", loglvl="quiet")
            except Exception:
                msg.error("Detected Linux distribution is not Debian-based, unable to launch.")
    # check if specified device is supported
    with open(Path(cfg.DIR_ROOT, "wrapper", "manifests", "devices.json")) as f:
        devices = json.load(f)
    if config.get("codename") not in devices.keys():
        msg.error("Unsupported device codename specified.")
    if config.get("command") == "bundle":
        # check Conan-related argument usage
        if config.get("package_type") != "conan" and config.get("conan_upload"):
            msg.error("Cannot use Conan-related arguments with non-Conan packaging\n")


def main(args: argparse.Namespace) -> None:
    # start preparing the environment
    os.chdir(cfg.DIR_ROOT)
    if args.clean_root:
        cm.root()
        sys.exit(0)
    os.environ["LOGLEVEL"] = args.loglvl
    # define env variable with kernel version
    with open(Path(cfg.DIR_ROOT, "pyproject.toml")) as f:
        os.environ["KVERSION"] = f.read().split("version = \"")[1].split("\"")[0]
    # store arguments as a set, to pass on to models
    arguments = vars(args)
    arguments["build_module"] = args.command
    params = {
        "build_module",
        "benv",
        "codename",
        "base",
        "lkv",
        "clean_image",
        "chroot",
        "package_type",
        "clean_kernel",
        "clean_assets",
        "rom_only",
        "conan_upload",
        "ksu",
    }
    passed_params = {}
    for key, value in arguments.items():
        if key in params:
            passed_params[key] = value
    # validate arguments
    validate_settings(config=passed_params)
    # setup output stream
    if args.command and args.outlog:
        msg.note(f"Writing output to {args.outlog}")
        if args.outlog in os.listdir():
            os.remove(args.outlog)
        os.environ["OSTREAM"] = args.outlog
        msg.outputstream()
    # determine the build
    match args.benv:
        case "docker":
            DockerEngine(config=passed_params).run()
        case "podman":
            PodmanEngine(config=passed_params).run()
        case "local":
            match args.command:
                case "kernel":
                    KernelBuilder(
                        codename = args.codename,
                        base = args.base,
                        lkv = args.lkv,
                        clean = args.clean_kernel,
                        ksu = args.ksu,
                    ).run()
                case "assets":
                    AssetsCollector(
                        codename = args.codename,
                        base = args.base,
                        chroot = args.chroot,
                        clean = args.clean_assets,
                        rom_only = args.rom_only,
                        ksu = args.ksu,
                    ).run()
                case "bundle":
                    BundleCreator(
                        codename = args.codename,
                        base = args.base,
                        lkv = args.lkv,
                        package_type = args.package_type,
                        ksu = args.ksu,
                    ).run()


if __name__ == "__main__":
    # for print's to show in the right order
    os.environ["PYTHONUNBUFFERED"] = "1"
    main(parse_args())
