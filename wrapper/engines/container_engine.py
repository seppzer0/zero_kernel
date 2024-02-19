import os
import shutil
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from subprocess import CompletedProcess

import wrapper.tools.messages as msg
import wrapper.tools.commands as ccmd

from wrapper.configs.directory_config import DirectoryConfig as dcfg

from wrapper.engines.interfaces import IContainerEngine


class ContainerEngine(BaseModel, IContainerEngine):
    """A generic container engine for containerized builds.

    Note that here paths from DirectoryConfig are not used
    directly. Because the build will run in a container,
    these paths will be redefined according to container's
    directory structure. We only need to specify directory
    names and not full paths.

    :param name_image: Name of the Docker/Podman image.
    :param name_container: Name of the Docker/Podman container.
    :param dir_kernel: Directory (name) for the kernel artifacts.
    :param dir_assets: Directory (name) for the assets artifacts.
    :param dir_bundle: Directory (name) for the bundle artifacts.
    :param wdir_container: Working directory in the container.
    :param wdir_local: Working directory from the local environment (aka root of the repo).
    :param benv: Build environment.
    :param module: Wrapper module to be launched.
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
    dir_kernel: Path = dcfg.kernel.name
    dir_assets: Path = dcfg.assets.name
    dir_bundle: Path = dcfg.bundle.name
    wdir_container: Path = Path("/", "zero_build")
    wdir_local: Path = dcfg.root

    benv: str
    module: str
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
        res = ""
        if os.getenv("CONAN_USER_HOME"):
            res = Path(os.getenv("CONAN_USER_HOME"))
        else:
            res = Path(os.getenv("HOME"), ".conan")
        return res

    @property
    def wrapper_cmd(self) -> str:
        # prepare launch command
        cmd = f"python3 {Path('wrapper', 'bridge.py')}"
        arguments = {
            "--module": self.module,
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
        if self.module == "bundle":
            if self.package_type in ("slim", "full"):
                cmd += f" && chmod 777 -R {Path(self.wdir_container, dcfg.bundle)}"
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
        # mount directories
        match self.module:
            case "kernel":
                options.append(
                    '-v {}/{}:{}/{}'.format(
                        dcfg.root,
                        dcfg.kernel,
                        self.wdir_container,
                        dcfg.kernel
                    )
                )
            case "assets":
                options.append(
                    '-v {}/{}:{}/{}'.format(
                        dcfg.root,
                        dcfg.assets,
                        self.wdir_container,
                        dcfg.assets
                    )
                )
            case "bundle":
                match self.package_type:
                    case "slim" | "full":
                        options.append(
                            '-v {}/{}:{}/{}'.format(
                                dcfg.root,
                                dcfg.bundle,
                                self.wdir_container,
                                dcfg.bundle
                            )
                        )
                    case "conan":
                        if self.conan_upload:
                            options.append('-e CONAN_UPLOAD_CUSTOM=1')
                        # determine the path to local Conan cache and check if it exists
                        if self.dir_bundle_conan.isdir():
                            options.append(f'-v {self.dir_bundle_conan}:/"/root/.conan"')
                        else:
                            msg.error("Could not find Conan local cache on the host machine.")
        return options

    def create_dirs(self) -> None:
        match self.module:
            case "kernel":
                kdir = Path(dcfg.kernel)
                if not kdir.isdir():
                    os.mkdir(kdir)
            case "assets":
                assetsdir = Path(dcfg.assets)
                if not assetsdir.isdir():
                    os.mkdir(assetsdir)
            case "bundle":
                if self.package_type in ("slim", "full"):
                    # mount directory with release artifacts
                    bdir = Path(dcfg.bundle)
                    shutil.rmtree(bdir, ignore_errors=True)
                    os.mkdir(bdir)

    def build(self) -> CompletedProcess:
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

    def run(self) -> None:
        self.build()
        # form the final command to create container
        cmd = '{} run {} {} /bin/bash -c "{}"'.format(
            self.benv,
            " ".join(self.container_options),
            self.name_image,
            self.wrapper_cmd
        )
        # prepare directories
        self.create_dirs()
        ccmd.launch(cmd)
        # navigate to root directory and clean image from host machine
        os.chdir(self.wdir_local)
        if self.clean_image:
            ccmd.launch(f"{self.benv} rmi {self.name_image}")
