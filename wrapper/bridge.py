import sys
import argparse

import wrapper.tools.messages as msg

from wrapper.commands.bundle import BundleCreator
from wrapper.commands.kernel import KernelBuilder
from wrapper.commands.assets import AssetsCollector

from wrapper.utils import ResourceManager


def parse_args() -> argparse.Namespace:
    """Parse arguments.

    Arguments here are NOT mandatory because this script has dual use:
    1) launch one of the commands: kernel, assets, bundle;
    2) install shared tools from tools.json.

    Because of that, all of the arguments are technically optional.
    Making any of the arguments mandatory would not allow it to be dual-use.
    """
    parser = argparse.ArgumentParser()
    args = None if sys.argv[1:] else ["-h"]
    parser.add_argument(
        "--command",
        help="select wrapper command",
        choices=("kernel", "assets", "bundle")
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
        choices=("full", "minimal")
    )
    parser.add_argument(
        "--package-type",
        dest="package_type",
        help="select bundle packaging type",
        choices=("conan", "slim", "full")
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
        "--shared",
        help="only setup the shared tools in the environment",
        action="store_true"
    )
    return parser.parse_args(args)


def main(args: argparse.Namespace) -> None:
    """Launch the bridge."""
    match args.command:
        case "kernel":
            KernelBuilder(
                codename = args.codename,
                base = args.base,
                lkv = args.lkv,
                clean_kernel = args.clean_kernel,
                ksu = args.ksu,
            ).run()
        case "assets":
            AssetsCollector(
                codename = args.codename,
                base = args.base,
                chroot = args.chroot,
                clean_assets = args.clean_assets,
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
        case _:
            # if no command was selected, then shared tools are (supposed to be) installed
            if args.shared:
                tconf = ResourceManager()
                tconf.path_gen()
                tconf.download()
            else:
                # technically this part of code cannot be reached and is just an extra precaution
                msg.error("Invalid argument set specified, please review")


if __name__ == "__main__":
    msg.outputstream()
    main(parse_args())
