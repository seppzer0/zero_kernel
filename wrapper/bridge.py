import sys
import argparse

import tools.messages as msg

from models.bundle import BundleCreator
from models.kernel import KernelBuilder
from models.assets import AssetCollector

from utils import Resources


def parse_args() -> argparse.Namespace:
    """Parse arguments."""
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
        "--rom",
        dest="rom",
        help="select a ROM for the build"
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
        "--extra-assets",
        dest="extra_assets",
        help="choose to download extra assets",
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
                rom = args.rom,
                clean = args.clean_kernel,
                ksu = args.ksu,
            ).run()
        case "assets":
            AssetCollector(
                codename = args.codename,
                rom = args.rom,
                chroot = args.chroot,
                clean = args.clean_assets,
                rom_only = args.rom_only,
                extra_assets = args.extra_assets,
                ksu = args.ksu,
            ).run()
        case "bundle":
            BundleCreator(
                codename = args.codename,
                rom = args.rom,
                package_type = args.package_type,
                ksu = args.ksu,
            ).run()
        case _:
            # if no module was selected, then the shared tools are installed
            tconf = Resources()
            tconf.path_gen()
            tconf.download()


if __name__ == "__main__":
    msg.outputstream()
    main(parse_args())
