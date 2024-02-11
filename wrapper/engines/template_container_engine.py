import os
import shutil
from pathlib import Path

import tools.messages as msg
import tools.commands as ccmd

from configs import Config as cfg


class TemplateContainerEngine:
    """A template engine for containerized builds."""

    benv: str
    name_image: str = "zero-kernel-image"
    name_container: str = "zero-kernel-container"
    dir_init: Path = Path.cwd()
    dir_kernel: Path = Path(cfg.DIR_KERNEL)
    dir_assets: Path = Path(cfg.DIR_ASSETS)
    dir_bundle: Path = Path(cfg.DIR_BUNDLE)
    wdir_container: Path = Path("/", "zero_build")
    wdir_local: Path = cfg.DIR_ROOT

    def __init__(self, config: dict) -> None:
        self.build_module = config.get("build_module")
        self.codename = config.get("codename")
        self.base = config.get("base")
        self.lkv = config.get("lkv")
        self.chroot = config.get("chroot", None)
        self.package_type = config.get("package_type", None)
        self.clean_image = config.get("clean_image", False)
        self.clean_kernel = config.get("clean_kernel", False)
        self.clean_assets = config.get("clean_assets", False)
        self.rom_only = config.get("rom_only", False)
        self.conan_upload = config.get("conan_upload", False)
        self.ksu = config.get("ksu", False)

    @property
    def dir_bundle_conan(self) -> Path:
        """Determine path to Conan's local cache."""
        res = ""
        if os.getenv("CONAN_USER_HOME"):
            res = Path(os.getenv("CONAN_USER_HOME"))
        else:
            res = Path(os.getenv("HOME"), ".conan")
        return res

    @property
    def wrapper_cmd(self) -> str:
        """Return the launch command for the wrapper."""
        # prepare launch command
        cmd = f"python3 {Path('wrapper', 'bridge.py')}"
        arguments = {
            "--build-module": self.build_module,
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
            if value not in (None, False, True):
                cmd += f" {arg}={value}"
            elif value in (True,):
                cmd += f" {arg}"
        # extend the command with the selected packaging option
        if self.build_module == "bundle":
            if self.package_type in ("slim", "full"):
                cmd += f" && chmod 777 -R {Path(self.wdir_container, self.dir_bundle)}"
            else:
                cmd += " && chmod 777 -R /root/.conan"
        return cmd

    @property
    def container_options(self) -> list[str]:
        """Form the arguments for container launch."""
        # declare the base
        options = [
            "-i",
            "--rm",
            "-e KVERSION={}".format(os.getenv("KVERSION")),
            "-e LOGLEVEL={}".format(os.getenv("LOGLEVEL")),
            "-w {}".format(self.wdir_container),
        ]
        # mount directories
        match self.build_module:
            case "kernel":
                options.append(
                    '-v {}/{}:{}/{}'.format(
                        cfg.DIR_ROOT,
                        self.dir_kernel,
                        self.wdir_container,
                        self.dir_kernel
                    )
                )
            case "assets":
                options.append(
                    '-v {}/{}:{}/{}'.format(
                        cfg.DIR_ROOT,
                        self.dir_assets,
                        self.wdir_container,
                        self.dir_assets
                    )
                )
            case "bundle":
                match self.package_type:
                    case "slim" | "full":
                        options.append(
                            '-v {}/{}:{}/{}'.format(
                                cfg.DIR_ROOT,
                                self.dir_bundle,
                                self.wdir_container,
                                self.dir_bundle
                            )
                        )
                    case "conan":
                        if self.conan_upload:
                            options.append('-e CONAN_UPLOAD_CUSTOM=1')
                        # determine the path to local Conan cache and check if it exists
                        if self.dir_bundle_conan.is_dir():
                            options.append(f'-v {self.dir_bundle_conan}:/"/root/.conan"')
                        else:
                            msg.error("Could not find Conan local cache on the host machine.")
        return options

    def create_dirs(self) -> None:
        """Create required directories for volume mounting."""
        match self.build_module:
            case "kernel":
                kdir = Path(cfg.DIR_KERNEL)
                if not kdir.is_dir():
                    os.mkdir(kdir)
            case "assets":
                assetsdir = Path(cfg.DIR_ASSETS)
                if not assetsdir.is_dir():
                    os.mkdir(assetsdir)
            case "bundle":
                if self.package_type in ("slim", "full"):
                    # mount directory with release artifacts
                    bdir = Path(cfg.DIR_BUNDLE)
                    shutil.rmtree(bdir, ignore_errors=True)
                    os.mkdir(bdir)

    def build(self) -> None:
        """Build the image."""
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
        ccmd.launch(cmd)
        msg.done("Done!")
        print("\n")

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
        os.chdir(self.dir_init)
        if self.clean_image:
            ccmd.launch(f"{self.benv} rmi {self.name_image}")
