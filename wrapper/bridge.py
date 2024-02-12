import sys
import argparse

import tools.messages as msg

from models.bundle_creator import BundleCreator
from models.kernel_builder import KernelBuilder
from models.assets_collector import AssetsCollector

from utils import Resources


def parse_args() -> argparse.Namespace:
    """Parse arguments.
    
    Arguments here are NOT required because this script has dual use:
    1) launch one of the modules: kernel, assets, bundle;
    2) install shared tools from tools.json.

    Making arguments required would force to specify all of them from both cases.
    """
    parser = argparse.ArgumentParser()
    args = None if sys.argv[1:] else ["-h"]
    parser.add_argument(
        "--build-module",
        dest="build_module",
        help="select module",
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
        "--tools",
        help="only setup the shared tools in the environment",
        action="store_true"
    )
    return parser.parse_args(args)


def main(args: argparse.Namespace) -> None:
    """Launch the bridge."""
    match args.build_module:
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
        case _:
            # if no module was selected, then shared tools are (supposed to be) installed
            if args.tools:
                tconf = Resources()
                tconf.path_gen()
                tconf.download()
            else:
                # technically this part of code cannot be reached and is just an extra precaution
                msg.error("Invalid argument set specified, please review")


if __name__ == "__main__":
    msg.outputstream()
    main(parse_args())
