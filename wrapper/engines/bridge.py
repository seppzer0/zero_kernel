import os
import sys
import argparse
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "models"))
from kernel import KernelBuilder
from assets import AssetCollector
from bundle import BundleCreator

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import messages as msg


def parse_args() -> None:
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-module",
                        dest="build_module",
                        required=True,
                        help="select module",
                        choices=["kernel", "assets", "bundle"])
    parser.add_argument("--codename",
                        dest="codename",
                        required=True,
                        help="select device codename")
    parser.add_argument("--losversion",
                        dest="losversion",
                        required=True,
                        help="select LineageOS version")
    parser.add_argument("--chroot",
                        help="select chroot type",
                        choices=["full", "minimal"])
    parser.add_argument("--package-type",
                        dest="package_type",
                        help="select bundle packaging type",
                        choices=["conan", "generic-slim"])
    parser.add_argument("--clean-kernel",
                        dest="clean_kernel",
                        help="clean kernel directory",
                        action="store_true")
    parser.add_argument("--clean-assets",
                        dest="clean_assets",
                        help="clean assets directory",
                        action="store_true")
    parser.add_argument("--rom-only",
                        dest="rom_only",
                        help="download only ROM for an asset",
                        action="store_true")
    parser.add_argument("--extra-assets",
                        dest="extra_assets",
                        help="choose to download extra assets",
                        action="store_true")
    global args
    args = parser.parse_args()


def launch() -> None:
    """Launch the bridge."""
    if args.build_module == "kernel":
        KernelBuilder(
            args.codename,
            args.losversion,
            args.clean_kernel
        )
    elif args.build_module == "assets":
        AssetCollector(
            args.codename,
            args.losversion,
            args.chroot,
            args.clean_assets,
            args.rom_only,
            args.extra_assets
        )
    elif args.build_module == "bundle":
        BundleCreator(
            args.codename,
            args.losversion,
            args.package_type
        )


parse_args()
msg.outputstream()
launch()
