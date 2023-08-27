import os
import shutil
from typing import List
from pathlib import Path

import wrapper.tools.messages as msg
import wrapper.tools.commands as ccmd


class ContainerEngine:
    """Use containers (Docker/Podman) for the build."""

    def __init__(self, config: dict) -> None:
        self._buildenv = config.get("buildenv")
        self._build_module = config.get("build_module")
        self._codename = config.get("codename")
        self._rom = config.get("rom")
        self._chroot = config.get("chroot", None)
        self._package_type = config.get("package_type", None)
        self._clean_image = config.get("clean_image", False)
        self._clean_kernel = config.get("clean_kernel", False)
        self._clean_assets = config.get("clean_assets", False)
        self._rom_only = config.get("rom_only", False)
        self._extra_assets = config.get("extra_assets", False)
        self._conan_upload = config.get("conan_upload", False)
        self._ksu = config.get("ksu", False)

    @property
    def _image_name(self) -> str:
        return "s0nh-docker-image"

    @property
    def _container_name(self) -> str:
        return "s0nh-docker-container"

    @property
    def _local_workdir(self) -> Path:
        return Path(os.getenv("ROOTPATH"))

    @property
    def _docker_workdir(self) -> str:
        return "s0nh_build"

    @property
    def _initial_dir(self) -> Path:
        return Path.cwd()

    @property
    def _dir_kernel(self) -> Path:
        return Path("kernel")

    @property
    def _dir_assets(self) -> Path:
        return Path("assets")

    @property
    def _dir_bundle_generic(self) -> Path:
        return Path(f"release-{self._package_type}")

    @property
    def _dir_bundle_conan(self) -> Path:
        res = ""
        if os.getenv("CONAN_USER_HOME"):
            res =  Path(os.getenv("CONAN_USER_HOME"))
        else:
            res = Path(os.getenv("HOME"), ".conan")
        return res

    @property
    def _wrapper_cmd(self) -> str:
        """Return the launch command for the wrapper."""
        # prepare launch command
        cmd = f"python3 {Path('wrapper', 'utils', 'bridge.py')}"
        arguments = {
            "--build-module": self._build_module,
            "--codename": self._codename,
            "--rom": self._rom,
            "--chroot": self._chroot,
            "--package-type": self._package_type,
            "--rom-only": self._rom_only,
            "--extra-assets": self._extra_assets,
            "--ksu": self._ksu,
        }
        # extend with arguments in mind
        for arg, value in arguments.items():
            if value not in (None, False, True):
                cmd += f" {arg}={value}"
            elif value in (True,):
                cmd += f" {arg}"
        # extend with packaging option in mind
        if self._build_module == "bundle":
            if self._package_type in ("slim", "full"):
                cmd += f" && chmod 777 -R /{Path(self._docker_workdir, self._dir_bundle_generic)}"
            else:
                cmd += " && chmod 777 -R /root/.conan"
        return cmd

    @property
    def _container_options(self) -> List[str]:
        """Form a list of Docker options to pass."""
        # declare a base of options
        options = [
            "-i",
            "--rm",
            "-e ROOTPATH=/{}".format(self._docker_workdir),
            "-w /{}".format(self._docker_workdir),
        ]
        # mount directories
        if self._build_module == "kernel":
            options.append(
                f'-v {os.getenv("ROOTPATH")}/{self._dir_kernel}:/{self._docker_workdir}/{self._dir_kernel}'
            )
        elif self._build_module == "assets":
            options.append(
                f'-v {os.getenv("ROOTPATH")}/{self._dir_assets}:/{self._docker_workdir}/{self._dir_assets}'
            )
        if self._build_module == "bundle":
            if self._package_type in ("slim", "full"):
                options.append(
                    f'-v {os.getenv("ROOTPATH")}/{self._dir_bundle_generic}:/{self._docker_workdir}/{self._dir_bundle_generic}'
                )
            elif self._package_type == "conan":
                if self._conan_upload:
                    options.append('-e CONAN_UPLOAD_CUSTOM=1')
                # determine the path to local Conan cache and check if it exists
                if self._dir_bundle_conan.is_dir():
                    options.append(f'-v {self._dir_bundle_conan}:/"/root/.conan"')
                else:
                    msg.error("Could not find Conan local cache on the host machine.")
        return options

    def _create_dirs(self) -> None:
        """Create required directories for volume mounting."""
        if self._build_module == "kernel":
            kdir = Path("kernel")
            if not kdir.is_dir():
                os.mkdir(kdir)
        elif self._build_module == "assets":
            assetsdir = Path("assets")
            if not assetsdir.is_dir():
                os.mkdir(assetsdir)
        if self._build_module == "bundle":
            if self._package_type in ("slim", "full"):
                # mount directory with release artifacts
                reldir_generic = f"release-{self._package_type}"
                shutil.rmtree(reldir_generic, ignore_errors=True)
                os.mkdir(reldir_generic)

    def run(self) -> None:
        os.chdir(self._local_workdir)
        # force enable Docker Buildkit to create Docker image
        if self._buildenv == "docker":
            os.environ["DOCKER_BUILDKIT"] = "1"
        cmd = f"{self._buildenv} build . -f {self._local_workdir / 'Dockerfile'} -t {self._image_name}"
        ccmd.launch(cmd)
        # form the final command
        cmd = f'{self._buildenv} run {" ".join(self._container_options)} {self._image_name} /bin/bash -c "{self._wrapper_cmd}"'
        # prepare directories if required
        self._create_dirs()
        ccmd.launch(cmd)
        # navigate to root directory and clean image from host machine
        os.chdir(self._initial_dir)
        if self._clean_image:
            ccmd.launch(f"{self._buildenv} rmi {self._image_name}")
