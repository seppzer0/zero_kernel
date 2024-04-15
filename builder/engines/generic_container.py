import os
import shutil
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from subprocess import CompletedProcess

from builder.tools import commands as ccmd, messages as msg
from builder.configs import DirectoryConfig as dcfg
from builder.interfaces import IGenericContainerEngine


class GenericContainerEngine(BaseModel, IGenericContainerEngine):
    """A generic container engine for containerized builds.

    Note that here paths from DirectoryConfig are not used
    directly. Because the build will run in a container,
    these paths will be redefined according to container's
    directory structure. We only need to specify directory
    names and not full paths.

    :param benv: Build environment.
    :param command: Builder command to be launched.
    :param codename: Device codename.
    :param base: Kernel source base.
    :param lkv: Linux kernel version.
    :param chroot: Chroot type.
    :param package_type: Package type.
    :param clean_kernel: Flag to clean folder for kernel storage.
    :param clean_assets: Flag to clean folder for assets storage.
    :param clean_image: Flag to clean a Docker/Podman image from local cache.
    :param rom_only: Flag indicating ROM-only asset collection.
    :param conan_upload: Flag to enable Conan upload.
    :param ksu: Flag to add KernelSU support into the kernel.
    """

    name_image: str = "zero-kernel-image"
    name_container: str = "zero-kernel-container"
    wdir_container: Path = Path("/", "zero_build")
    wdir_local: Path = dcfg.root

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

    @property
    def dir_bundle_conan(self) -> Path:
        if os.getenv("CONAN_USER_HOME"):
            return Path(os.getenv("CONAN_USER_HOME"))
        else:
            return Path(os.getenv("HOME"), ".conan")

    @property
    def builder_cmd(self) -> str:
        # prepare launch command
        cmd = f"python3 {Path('builder', 'utils', 'bridge.py')}"
        arguments = {
            "--command": self.command,
            "--codename": self.codename,
            "--base": self.base,
            "--lkv": self.lkv,
            "--chroot": self.chroot,
            "--package-type": self.package_type,
            "--rom-only": self.rom_only,
            "--ksu": self.ksu,
            "--clean-kernel": self.clean_kernel,
            "--clean-assets": self.clean_assets,
        }
        # extend the command with given arguments
        for arg, value in arguments.items():
            # arguments that have a string value
            if value not in (None, False, True):
                cmd += f" {arg}={value}"
            # arguments that act like boolean switches
            elif value:
                cmd += f" {arg}"
        # extend the command with the selected packaging option
        if self.command == "bundle":
            if self.package_type in ("slim", "full"):
                cmd += f" && chmod 777 -R {self.wdir_container / dcfg.bundle.name}"
            else:
                cmd += " && chmod 777 -R /root/.conan"
        return cmd

    @property
    def container_options(self) -> list[str]:
        # declare the base
        options = [
            "-i",
            "--rm",
            "-e KVERSION={}".format(os.getenv("KVERSION")),
            "-e LOGLEVEL={}".format(os.getenv("LOGLEVEL")),
            "-w {}".format(self.wdir_container),
        ]
        # define volume mounting template
        v_template = "-v {}:{}/{}"
        # mount directories
        match self.command:
            case "kernel":
                options.append(v_template.format(dcfg.kernel, self.wdir_container, dcfg.kernel.name))
            case "assets":
                options.append(v_template.format(dcfg.assets, self.wdir_container, dcfg.assets.name))
            case "bundle":
                match self.package_type:
                    case "slim" | "full":
                        options.append(v_template.format(dcfg.bundle, self.wdir_container, dcfg.bundle.name))
                    case "conan":
                        if self.conan_upload:
                            options.append("-e CONAN_UPLOAD_CUSTOM=1")
                        # determine the path to local Conan cache and check if it exists
                        if self.dir_bundle_conan.is_dir():
                            options.append(f'-v {self.dir_bundle_conan}:/"/root/.conan"')
                        else:
                            msg.error("Could not find Conan local cache on the host machine.")
        return options

    def create_dirs(self) -> None:
        match self.command:
            case "kernel":
                if not dcfg.kernel.is_dir():
                    os.mkdir(dcfg.kernel)
            case "assets":
                if not dcfg.assets.is_dir():
                    os.mkdir(dcfg.assets)
            case "bundle":
                if self.package_type in ("slim", "full"):
                    # mount directory with release artifacts
                    shutil.rmtree(dcfg.bundle, ignore_errors=True)
                    os.mkdir(dcfg.bundle)

    def build_image(self) -> CompletedProcess:
        print("\n")
        alias = self.benv.capitalize()
        msg.note(f"Building the {alias} image..")
        os.chdir(self.wdir_local)
        # NOTE: this will crash in GitLab CI/CD (Docker-in-Docker), requires a workaround
        cmd = "{} build . -f {} -t {} --load".format(
            self.benv,
            self.wdir_local / 'Dockerfile',
            self.name_image
        )
        res = ccmd.launch(cmd)
        msg.done("Done!")
        print("\n")
        return res

    @property
    def run_cmd(self) -> str:
        return '{} run {} {} /bin/bash -c "{}"'.format(
            self.benv,
            " ".join(self.container_options),
            self.name_image,
            self.builder_cmd
        )

    def __enter__(self) -> None:
        # build the image and prepare directories
        self.build_image()
        self.create_dirs()

    def __exit__(self) -> None:
        # navigate to root directory and clean image from host machine
        os.chdir(self.wdir_local)
        if self.clean_image:
            ccmd.launch(f"{self.benv} rmi {self.name_image}")
