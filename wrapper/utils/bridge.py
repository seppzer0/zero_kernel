import sys
import argparse

import wrapper.tools.messages as msg

from wrapper.models.kernel import KernelBuilder
from wrapper.models.assets import AssetCollector
from wrapper.models.bundle import BundleCreator


def parse_args() -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    args = None if sys.argv[1:] else ["-h"]
    parser.add_argument(
        "--build-module",
        dest="build_module",
        required=True,
        help="select module",
        choices=["kernel", "assets", "bundle"]
    )
    parser.add_argument(
        "--codename",
        dest="codename",
        required=True,
        help="select device codename"
    )
    parser.add_argument(
        "--losversion",
        dest="losversion",
        required=True,
        help="select LineageOS version"
    )
    parser.add_argument(
        "--chroot",
        help="select chroot type",
        choices=["full", "minimal"]
    )
    parser.add_argument(
        "--package-type",
        dest="package_type",
        help="select bundle packaging type",
        choices=["conan", "generic-slim"]
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
    return parser.parse_args(args)


def main(args: argparse.Namespace) -> None:
    """Launch the bridge."""
    if args.build_module == "kernel":
        KernelBuilder(
            args.codename,
            args.losversion,
            args.clean_kernel
        ).run()
    elif args.build_module == "assets":
        AssetCollector(
            args.codename,
            args.losversion,
            args.chroot,
            args.clean_assets,
            args.rom_only,
            args.extra_assets
        ).run()
    elif args.build_module == "bundle":
        BundleCreator(
            args.codename,
            args.losversion,
            args.package_type
        ).run()


if __name__ == "__main__":
    msg.outputstream()
    main(parse_args())
