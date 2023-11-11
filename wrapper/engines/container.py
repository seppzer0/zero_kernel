import os
import shutil
from pathlib import Path

import tools.messages as msg
import tools.commands as ccmd

from configs import Config as cfg


class ContainerEngine:
    """Use containers (Docker/Podman) for the build."""

    _name_image: str = "zero-kernel-image"
    _name_container: str = "zero-kernel-container"
    _dir_init: Path = Path.cwd()
    _dir_kernel: Path = Path(cfg.DIR_KERNEL)
    _dir_assets: Path = Path(cfg.DIR_ASSETS)
    _dir_bundle: Path = Path(cfg.DIR_BUNDLE)
    _wdir_docker: Path = Path("/", "zero_build")
    _wdir_local: Path = cfg.DIR_ROOT

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
    def _dir_bundle_conan(self) -> Path:
        """Determine path to Conan's local cache."""
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
        cmd = f"python3 {Path('wrapper', 'bridge.py')}"
        arguments = {
            "--build-module": self._build_module,
            "--codename": self._codename,
            "--rom": self._rom,
            "--chroot": self._chroot,
            "--package-type": self._package_type,
            "--rom-only": self._rom_only,
            "--extra-assets": self._extra_assets,
            "--ksu": self._ksu,
            "--clean-kernel": self._clean_kernel,
            "--clean-assets": self._clean_assets,
        }
        # extend the command with given arguments
        for arg, value in arguments.items():
            if value not in (None, False, True):
                cmd += f" {arg}={value}"
            elif value in (True,):
                cmd += f" {arg}"
        # extend the command with the selected packaging option
        if self._build_module == "bundle":
            if self._package_type in ("slim", "full"):
                cmd += f" && chmod 777 -R {Path(self._wdir_docker, self._dir_bundle)}"
            else:
                cmd += " && chmod 777 -R /root/.conan"
        return cmd

    @property
    def _container_options(self) -> list[str]:
        """Form the list of Docker options."""
        # declare the base
        options = [
            "-i",
            "--rm",
            "-e KVERSION={}".format(os.getenv("KVERSION")),
            "-e LOGLEVEL={}".format(os.getenv("LOGLEVEL")),
            "-w {}".format(self._wdir_docker),
        ]
        # mount directories
        match self._build_module:
            case "kernel":
                options.append(
                    '-v {}/{}:{}/{}'.format(
                        cfg.DIR_ROOT,
                        self._dir_kernel,
                        self._wdir_docker,
                        self._dir_kernel
                    )
                )
            case "assets":
                options.append(
                    '-v {}/{}:{}/{}'.format(
                        cfg.DIR_ROOT,
                        self._dir_assets,
                        self._wdir_docker,
                        self._dir_assets
                    )
                )
            case "bundle":
                match self._package_type:
                    case "slim" | "full":
                        options.append(
                            '-v {}/{}:{}/{}'.format(
                                cfg.DIR_ROOT,
                                self._dir_bundle,
                                self._wdir_docker,
                                self._dir_bundle
                            )
                        )
                    case "conan":
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
        match self._build_module:
            case "kernel":
                kdir = Path(cfg.DIR_KERNEL)
                if not kdir.is_dir():
                    os.mkdir(kdir)
            case "assets":
                assetsdir = Path(cfg.DIR_ASSETS)
                if not assetsdir.is_dir():
                    os.mkdir(assetsdir)
            case "bundle":
                if self._package_type in ("slim", "full"):
                    # mount directory with release artifacts
                    bdir = Path(cfg.DIR_BUNDLE)
                    shutil.rmtree(bdir, ignore_errors=True)
                    os.mkdir(bdir)

    def _build(self) -> None:
        """Build the Docker/Podman image."""
        print("\n")
        alias = self._buildenv.capitalize()
        msg.note(f"Building the {alias} image..")
        os.chdir(self._wdir_local)
        # build only if it is not present in local cache
        # TODO: find a way to remove this slug for the command to work in GitLab CI/CD (Docker-in-Docker)
        #if self._name_image not in ccmd.launch(f"{self._buildenv} image list --format '{{.Repository}}'", get_output=True):
        if "slug" == "slug":
            # force enable Docker Buildkit
            if self._buildenv == "docker":
                os.environ["DOCKER_BUILDKIT"] = "1"
            cmd = "{} build . -f {} -t {} --load".format(
                self._buildenv,
                self._wdir_local / 'Dockerfile',
                self._name_image
            )
            ccmd.launch(cmd)
            msg.done("Done!")
        else:
            msg.note(f"{alias} image is already present, skipping the build.")
        print("\n")

    def run(self) -> None:
        self._build()
        # form the final "docker/podman run" command
        cmd = '{} run {} {} /bin/bash -c "{}"'.format(
            self._buildenv,
            " ".join(self._container_options),
            self._name_image,
            self._wrapper_cmd
        )
        # prepare directories
        self._create_dirs()
        ccmd.launch(cmd)
        # navigate to root directory and clean image from host machine
        os.chdir(self._dir_init)
        if self._clean_image:
            ccmd.launch(f"{self._buildenv} rmi {self._name_image}")
