import os
import io
import sys
import json
import argparse
from pathlib import Path
from importlib.metadata import version

from builder.core import KernelBuilder, AssetsCollector
from builder.tools import cleaning as cm, commands as ccmd, Logger as logger
from builder.configs import ArgumentConfig, DirectoryConfig as dcfg
from builder.engines import GenericContainerEngine
from builder.commands import KernelCommand, AssetsCommand, BundleCommand
from builder.managers import ResourceManager


def __get_version() -> str:
    """Get app version.

    Version is retrieved depending on the way the app
    is launched (as PIP package or from source).

    :return: App version.
    :rtype: str
    """
    msg = "zero_kernel {}"

    try:
        return msg.format(version("zero-kernel"))
    except Exception:
        with open(Path(__file__).absolute().parents[1] / "pyproject.toml", "r") as f:
            v = f.read().split('version = "')[1].split('"')[0]
        return msg.format(v)


def parse_args() -> argparse.Namespace:
    """Parse the script arguments.

    :return: Namespace of arguments.
    :rtype: argparse.Namespace
    """
    # show the 'help' message if no arguments supplied
    args = None if sys.argv[1:] else ["-h"]

    # parser and subparsers
    parser_parent = argparse.ArgumentParser(description="Advanced Android kernel builder with Kali NetHunter support.")
    subparsers = parser_parent.add_subparsers(dest="command")
    parser_kernel = subparsers.add_parser("kernel", help="build the kernel")
    parser_assets = subparsers.add_parser("assets", help="collect assets")
    parser_bundle = subparsers.add_parser("bundle", help="build the kernel + collect assets")

    # main parser arguments
    parser_parent.add_argument(
        "--clean",
        dest="clean_root",
        action="store_true",
        help="clean the root directory"
    )
    parser_parent.add_argument("-v", "--version", action="version", version=__get_version())

    # common argument attributes for subparsers
    help_base = "select a kernel base for the build"
    help_codename = "select device codename"
    help_benv = "select build environment"
    help_clean = "remove Docker/Podman image from the host machine after build"
    choices_benv = {"local", "docker", "podman"}
    choices_base = {"los", "pa", "x", "aosp"}
    help_defconfig = "specify path to custom defconfig"
    help_ksu = "add KernelSU support"
    help_lkv = "select Linux Kernel Version"

    # kernel
    parser_kernel.add_argument(
        "--build-env",
        type=str,
        dest="benv",
        required=True,
        choices=choices_benv,
        help=help_benv,
    )
    parser_kernel.add_argument(
        "--base",
        type=str,
        required=True,
        help=help_base,
        choices=choices_base
    )
    parser_kernel.add_argument(
        "--codename",
        type=str,
        required=True,
        help=help_codename
    )
    parser_kernel.add_argument(
        "--lkv",
        type=str,
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
        "--ksu",
        action="store_true",
        dest="ksu",
        help=help_ksu
    )
    parser_kernel.add_argument(
        "--defconfig",
        type=Path,
        dest="defconfig",
        help=help_defconfig
    )

    # assets
    parser_assets.add_argument(
        "--build-env",
        type=str,
        dest="benv",
        required=True,
        choices=choices_benv,
        help=help_benv
    )
    parser_assets.add_argument(
        "--base",
        type=str,
        required=True,
        help=help_base,
        choices=choices_base
    )
    parser_assets.add_argument(
        "--codename",
        type=str,
        required=True,
        help=help_codename
    )
    parser_assets.add_argument(
        "--chroot",
        type=str,
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
        "--ksu",
        action="store_true",
        dest="ksu",
        help=help_ksu
    )

    # bundle
    parser_bundle.add_argument(
        "--build-env",
        type=str,
        dest="benv",
        required=True,
        choices=choices_benv,
        help=help_benv
    )
    parser_bundle.add_argument(
        "--base",
        type=str,
        required=True,
        help=help_base,
        choices=choices_base
    )
    parser_bundle.add_argument(
        "--codename",
        type=str,
        required=True,
        help=help_codename
    )
    parser_bundle.add_argument(
        "--lkv",
        type=str,
        required=True,
        help=help_lkv
    )
    parser_bundle.add_argument(
        "--package-type",
        type=str,
        required=True,
        dest="package_type",
        choices={"conan", "slim", "full"},
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
        "--ksu",
        action="store_true",
        dest="ksu",
        help=help_ksu
    )
    parser_bundle.add_argument(
        "--defconfig",
        type=Path,
        dest="defconfig",
        help=help_defconfig
    )
    return parser_parent.parse_args(args)


def main(args: argparse.Namespace) -> None:
    # initialize the logger in memory
    _ = logger().get_logger()  # type: ignore
    # start preparing the environment
    os.chdir(dcfg.root)
    if args.clean_root:
        cm.root()
        sys.exit(0)

    # define env variable with kernel version
    with open(dcfg.root / "pyproject.toml", encoding="utf-8") as f:
        os.environ["KVERSION"] = f.read().split('version = "')[1].split('"')[0]

    # create a config for checking and storing arguments
    if args.command != "assets" and args.defconfig:
        args.defconfig = args.defconfig if args.defconfig.is_absolute() else Path.cwd() / args.defconfig
    arguments = vars(args)
    acfg = ArgumentConfig(**arguments)
    acfg.check_settings()

    # determine the build variation
    match args.benv:
        case "docker" | "podman":
            with GenericContainerEngine(**json.loads(acfg.model_dump_json())) as engined_cmd:
                ccmd.launch(engined_cmd)

        case "local":
            kernel_builder = KernelBuilder(
                codename = args.codename,
                base = args.base,
                lkv = args.lkv,
                clean_kernel = args.clean_kernel,
                ksu = args.ksu,
                defconfig = args.defconfig,
                rmanager = ResourceManager(
                    codename = args.codename,
                    lkv = args.lkv,
                    base = args.base
                )
            )
            assets_collector = AssetsCollector(
                codename = args.codename,
                base = args.base,
                chroot = args.chroot,
                clean_assets = args.clean_assets,
                rom_only = args.rom_only,
                ksu = args.ksu,
            )

            match args.command:
                case "kernel":
                    kc = KernelCommand(kernel_builder=kernel_builder)
                    kc.execute()

                case "assets":
                    ac = AssetsCommand(assets_collector=assets_collector)
                    ac.execute()

                case "bundle":  
                    bc = BundleCommand(
                        kernel_builder = kernel_builder,
                        assets_collector = assets_collector,
                        package_type = args.package_type,
                        base = args.base
                    )
                    bc.execute()


if __name__ == "__main__":
    # for logs to show in the right order in various build / CI/CD systems
    sys.stdout = io.TextIOWrapper(open(sys.stdout.fileno(), "wb", 0), write_through=True)
    main(parse_args())
