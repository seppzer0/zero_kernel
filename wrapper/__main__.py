import os
import sys
import json
import argparse
from pathlib import Path

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg

from wrapper.modules.bundle_creator import BundleCreator
from wrapper.modules.kernel_builder import KernelBuilder
from wrapper.modules.assets_collector import AssetsCollector

from wrapper.configs import ArgumentConfig
from wrapper.configs.directory_config import DirectoryConfig as dcfg

from wrapper.engines.docker_engine import DockerEngine
from wrapper.engines.podman_engine import PodmanEngine


def parse_args() -> argparse.Namespace:
    """Parse the script arguments."""
    # show the 'help' message if no arguments supplied
    args = None if sys.argv[1:] else ["-h"]
    # parser and subparsers
    parser_parent = argparse.ArgumentParser(description="A custom wrapper for the zero kernel.")
    subparsers = parser_parent.add_subparsers(dest="module")
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
        help="don't build anything, only clean kernel directories"
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


def main(args: argparse.Namespace) -> None:
    # start preparing the environment
    os.chdir(dcfg.root)
    if args.clean_root:
        cm.root()
        sys.exit(0)
    os.environ["LOGLEVEL"] = args.loglvl
    # define env variable with kernel version
    with open(Path(dcfg.root, "pyproject.toml")) as f:
        os.environ["KVERSION"] = f.read().split("version = \"")[1].split("\"")[0]
    # create a config for argument check and storage
    arguments = vars(args)
    acfg = ArgumentConfig(**arguments)
    acfg.check_settings()
    # setup output stream
    if args.module and args.outlog:
        msg.note(f"Writing output to {args.outlog}")
        if args.outlog in os.listdir():
            os.remove(args.outlog)
        os.environ["OSTREAM"] = args.outlog
        msg.outputstream()
    # determine the build
    match args.benv:
        case "docker":
            DockerEngine(**json.loads(acfg.model_dump_json())).run()
        case "podman":
            PodmanEngine(**json.loads(acfg.model_dump_json())).run()
        case "local":
            match args.module:
                case "kernel":
                    KernelBuilder(
                        codename = acfg.codename,
                        base = acfg.base,
                        lkv = acfg.lkv,
                        clean_kernel = acfg.clean_kernel,
                        ksu = acfg.ksu,
                    ).run()
                case "assets":
                    AssetsCollector(
                        codename = acfg.codename,
                        base = acfg.base,
                        chroot = acfg.chroot,
                        clean_assets = acfg.clean_assets,
                        rom_only = acfg.rom_only,
                        ksu = acfg.ksu,
                    ).run()
                case "bundle":
                    BundleCreator(
                        codename = acfg.codename,
                        base = acfg.base,
                        lkv = acfg.lkv,
                        package_type = acfg.package_type,
                        ksu = acfg.ksu,
                    ).run()


if __name__ == "__main__":
    # for print's to show in the right order
    os.environ["PYTHONUNBUFFERED"] = "1"
    main(parse_args())
