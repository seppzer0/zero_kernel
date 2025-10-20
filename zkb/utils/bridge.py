"""
Bridge-connector to launch shift the build process from host to Docker/Podman container.

Essentially it re-launches the same builder, but the one that is a copy inside the container.
Complete chain is: builder in host -> this bridge -> builder in container.
"""

import sys
import logging
import argparse

from zkb.core import KernelBuilder, AssetsCollector
from zkb.managers import ResourceManager
from zkb.commands import KernelCommand, AssetsCommand, BundleCommand


log = logging.getLogger("ZeroKernelLogger")


def parse_args() -> argparse.Namespace:
    """Parse arguments.

    Arguments here are NOT mandatory because this script has dual use:
    1) launch one of the commands: kernel, assets, bundle;
    2) install shared tools from tools.json.

    Because of that, all of the arguments are technically optional.
    Making any of the arguments mandatory would not allow it to be dual-use.

    :return: Namespace of arguments.
    :rtype: argparse.Namespace
    """
    args = None if sys.argv[1:] else ["-h"]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--command",
        help="select builder command",
        choices={"kernel", "assets", "bundle"}
    )
    parser.add_argument(
        "--codename",
        help="select device codename"
    )
    parser.add_argument(
        "--base",
        help="select a kernel base for the build"
    )
    parser.add_argument(
        "--lkv",
        help="select Linux kernel version"
    )
    parser.add_argument(
        "--chroot",
        help="select chroot type",
        choices={"full", "minimal"}
    )
    parser.add_argument(
        "--package-type",
        dest="package_type",
        help="select bundle packaging type",
        choices={"conan", "slim", "full"}
    )
    parser.add_argument(
        "--clean-kernel",
        dest="clean_kernel",
        help="clean kernel directory",
        action="store_true"
    )
    parser.add_argument(
        "--clean-assets",
        dest="clean_assets",
        help="clean assets directory",
        action="store_true"
    )
    parser.add_argument(
        "--rom-only",
        dest="rom_only",
        help="download only ROM for an asset",
        action="store_true"
    )
    parser.add_argument(
        "--ksu",
        help="add KernelSU support",
        action="store_true"
    )
    parser.add_argument(
        "--defconfig",
        dest="defconfig",
        help="specify path to custom defconfig",
    )
    parser.add_argument(
        "--shared",
        help="only setup the shared tools in the environment",
        action="store_true"
    )

    return parser.parse_args(args)


def main(args: argparse.Namespace) -> None:

    match args.command:

        case "kernel":
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
            kc = KernelCommand(kernel_builder=kernel_builder)
            kc.execute()

        case "assets":
            assets_collector = AssetsCollector(
                codename = args.codename,
                base = args.base,
                chroot = args.chroot,
                clean_assets = args.clean_assets,
                rom_only = args.rom_only,
                ksu = args.ksu,
            )
            ac = AssetsCommand(assets_collector=assets_collector)
            ac.execute()

        case "bundle":
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
            bc = BundleCommand(
                kernel_builder = kernel_builder,
                assets_collector = assets_collector,
                package_type = args.package_type,
                base = args.base
            )
            bc.execute()

        case _:
            # if no command was selected, then shared tools are (supposed to be) installed
            if args.shared:
                rm = ResourceManager()
                rm.read_data()
                rm.generate_paths()
                rm.download()

            else:
                # technically this part of code cannot be reached and is just an extra precaution
                log.error("Invalid argument set specified, please review")
                sys.exit(1)


if __name__ == "__main__":
    main(parse_args())
