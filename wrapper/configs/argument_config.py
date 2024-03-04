import json
import platform
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from wrapper.tools import commands as ccmd
from wrapper.utils import messages as msg


class ArgumentConfig(BaseModel):
    """A variable storage to use across the application.

    :param benv: Build environment.
    :param command: Wrapper command to be launched.
    :param codename: Device codename.
    :param base: Kernel source base.
    :param lkv: Linux kernel version.
    :param chroot: Chroot type.
    :param package_type: Package type.
    :param clean_kernel: Flag to clean folder with kernel sources.
    :param clean_assets: Flag to clean folder for assets storage.
    :param clean_image: Flag to clean a Docker/Podman image from local cache.
    :param rom_only: Flag indicating ROM-only asset collection.
    :param conan_upload: Flag to enable Conan upload.
    :param ksu: Flag indicating KernelSU support.
    """

    benv: str
    command: str
    codename: str
    base: str
    lkv: Optional[str] = None
    chroot: Optional[str] = None
    package_type: Optional[str] = None
    clean_kernel: Optional[bool] = False
    clean_assets: Optional[bool] = False
    clean_image: Optional[bool] = False
    rom_only: Optional[bool] = False
    conan_upload: Optional[bool] = False
    ksu: Optional[bool] = False

    def check_settings(self) -> None:
        """Run settings validations."""
        # allow only asset colletion on a non-Linux machine
        if self.benv == "local" and self.command in ("kernel", "bundle"):
            if not platform.system() == "Linux":
                msg.error("Can't build kernel on a non-Linux machine.")
            else:
                # check that it is Debian-based
                try:
                    ccmd.launch("apt --version", loglvl="quiet")
                except Exception:
                    msg.error("Detected Linux distribution is not Debian-based.")
        # check if specified device is supported
        with open(Path(__file__).absolute().parents[2] / "wrapper" / "manifests" / "devices.json") as f:
            devices = json.load(f)
        if self.codename not in devices.keys():
            msg.error("Unsupported device codename specified.")
        if self.command == "bundle":
            # check Conan-related argument usage
            if self.package_type != "conan" and self.conan_upload:
                msg.error("Cannot use Conan-related arguments with non-Conan packaging\n")
