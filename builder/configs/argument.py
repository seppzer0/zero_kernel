import sys
import json
import logging
import platform
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Literal

from builder.tools import Logger, commands as ccmd


log = logging.getLogger("ZeroKernelLogger")


class ArgumentConfig(BaseModel):
    """Variable storage for usage across the app.

    :param Literal["docker","podman","local"] benv: Build environment.
    :param Literal["kernel","assets","bundle"] command: Builder command to be launched.
    :param str codename: Device codename.
    :param str base: Kernel source base.
    :param str lkv: Linux kernel version.
    :param Optional[str]=None chroot: Chroot type.
    :param Optional[str]=None package_type: Package type.
    :param Optional[bool]=False clean_kernel: Flag to clean folder with kernel sources.
    :param Optional[bool]=False clean_assets: Flag to clean folder for assets storage.
    :param Optional[bool]=False clean_image: Flag to clean a Docker/Podman image from local cache.
    :param Optional[bool]=False rom_only: Flag indicating ROM-only asset collection.
    :param Optional[bool]=False conan_upload: Flag to enable Conan upload.
    :param Optional[bool]=False ksu: Flag indicating KernelSU support.
    :param Optional[Path]=None defconfig: Path to custom defconfig.
    """

    benv: Literal["docker", "podman", "local"]
    command: Literal["kernel", "assets", "bundle"]
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
    defconfig: Optional[Path] = None

    def check_settings(self) -> None:
        """Run settings validations.

        :return: None
        """
        # allow only asset colletion on a non-Linux machine
        if self.benv == "local" and self.command in {"kernel", "bundle"}:
            if not platform.system() == "Linux":
                log.error("Can't build kernel on a non-Linux machine.")
                sys.exit(1)
            else:
                # check that it is Debian-based
                try:
                    ccmd.launch("apt --version", loglvl="quiet")
                except Exception:
                    log.error("Detected Linux distribution is not Debian-based.")
                    sys.exit(1)

        # check if specified device is supported
        with open(
            Path(__file__).absolute().parents[2] / "builder" / "manifests" / "devices.json", encoding="utf-8"
        ) as f:
            devices = json.load(f)

        if self.codename not in devices.keys():
            log.error("Unsupported device codename specified.")
            sys.exit(1)
        if self.command == "bundle":
            # check Conan-related argument usage
            if self.package_type != "conan" and self.conan_upload:
                log.error("Cannot use Conan-related arguments with non-Conan packaging\n")
                sys.exit(1)

        # check that the provided defconfig file is valid
        if self.defconfig and not self.defconfig.is_file():
            log.error("Provided path to defconfig is invalid.")
            sys.exit(1)
