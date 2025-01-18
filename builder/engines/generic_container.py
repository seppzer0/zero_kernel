import os
import shutil
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Literal
from subprocess import CompletedProcess

from builder.tools import commands as ccmd, messages as msg
from builder.configs import DirectoryConfig as dcfg
from builder.interfaces import IGenericContainerEngine


class GenericContainerEngine(BaseModel, IGenericContainerEngine):
    """Generic container engine for containerized builds.

    Note that here paths from DirectoryConfig are not used
    directly. Because the build will run in a container,
    these paths will be redefined according to container's
    directory structure. We don't need to pass full paths
    relevant to local environment, only directories' names.

    :param Literal["docker","podman"] benv: Build environment.
    :param Literal["kernel","assets","bundle"] command: Builder command to be launched.
    :param str codename: Device codename.
    :param str base: Kernel source base.
    :param str lkv: Linux kernel version.
    :param Optional[Literal["full","minimal"]]=None chroot: Chroot type.
    :param Optional[bool]=False package_type: Package type.
    :param Optional[bool]=False clean_kernel: Flag to clean folder for kernel storage.
    :param Optional[bool]=False clean_assets: Flag to clean folder for assets storage.
    :param Optional[bool]=False clean_image: Flag to clean a Docker/Podman image from local cache.
    :param Optional[bool]=False rom_only: Flag indicating ROM-only asset collection.
    :param Optional[bool]=False conan_upload: Flag to enable Conan upload.
    :param Optional[bool]=False ksu: Flag to add KernelSU support into the kernel.
    :param Optional[Path]=None defconfig: Path to custom defconfig.
    """

    _name_image: str = "zero-kernel-image"
    _name_container: str = "zero-kernel-container"
    _wdir_container: Path = Path("/", "zero_build")
    _wdir_local: Path = dcfg.root

    benv: Literal["docker", "podman"]
    command: Literal["kernel", "assets", "bundle"]
    codename: str
    base: str
    lkv: Optional[str] = None
    chroot: Optional[Literal["full", "minimal"]] = None
    package_type: Optional[str] = None
    clean_kernel: Optional[bool] = False
    clean_assets: Optional[bool] = False
    clean_image: Optional[bool] = False
    rom_only: Optional[bool] = False
    conan_upload: Optional[bool] = False
    ksu: Optional[bool] = False
    defconfig: Optional[Path] = None

    @staticmethod
    def _force_buildkit() -> None:
        """Force enable Docker BuildKit."""
        os.environ["DOCKER_BUILDKIT"] = "1"

    @property
    def dir_bundle_conan(self) -> Path:
        if os.getenv("CONAN_USER_HOME"):
            return Path(os.getenv("CONAN_USER_HOME")) # type: ignore
        else:
            return Path(os.getenv("HOME"), ".conan")  # type: ignore

    def check_cache(self) -> bool:
        img_cache_cmd = f'{self.benv} images --format {"{{.Repository}}"}'
        img_cache = str(ccmd.launch(img_cache_cmd, get_output=True))

        return True if self._name_image in img_cache else False

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
            "--defconfig": self.defconfig,
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
                cmd += f" && chmod 777 -R {self._wdir_container / dcfg.bundle.name}"
            else:
                cmd += " && chmod 777 -R /root/.conan"

        return cmd

    @property
    def container_options(self) -> list[str]:
        # declare the base of options
        options = [
            "-i",
            "--rm",
            "-e KVERSION={}".format(os.getenv("KVERSION")),
            "-e LOGLEVEL={}".format(os.getenv("LOGLEVEL")),
            "-w {}".format(self._wdir_container),
        ]

        # define volume mounting template
        v_template = "-v {}:{}/{}"

        # mount directories
        match self.command:
            case "kernel":
                options.append(v_template.format(dcfg.kernel, self._wdir_container, dcfg.kernel.name))
            case "assets":
                options.append(v_template.format(dcfg.assets, self._wdir_container, dcfg.assets.name))
            case "bundle":
                match self.package_type:
                    case "slim" | "full":
                        options.append(v_template.format(dcfg.bundle, self._wdir_container, dcfg.bundle.name))
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
                    os.makedirs(dcfg.kernel)
            case "assets":
                if not dcfg.assets.is_dir():
                    os.makedirs(dcfg.assets)
            case "bundle":
                if self.package_type in ("slim", "full"):
                    # mount directory with release artifacts
                    shutil.rmtree(dcfg.bundle, ignore_errors=True)
                    os.makedirs(dcfg.bundle)

    def build_image(self) -> str | None | CompletedProcess:
        print("\n")
        msg.note(f"Building the {self.benv.capitalize()} image..")

        os.chdir(self._wdir_local)
        # NOTE: this will crash in GitLab CI/CD (Docker-in-Docker), requires a workaround
        cmd = "{} build . -f {} -t {} --load".format(
            self.benv,
            self._wdir_local / "Dockerfile",
            self._name_image
        )

        res = ccmd.launch(cmd)
        msg.done("Done!")
        print("\n")

        return res

    @property
    def get_container_cmd(self) -> str:
        return '{} run {} {} /bin/bash -c "source .venv/bin/activate && {}"'.format(
            self.benv,
            " ".join(self.container_options),
            self._name_image,
            self.builder_cmd
        )

    def __enter__(self) -> str:
        # prepare Docker if selected
        if self.benv == "docker":
            self._force_buildkit()

        # build the image and prepare directories
        if not self.check_cache():
            self.build_image()
        else:
            msg.note(f"\n{self.benv.capitalize()} image already in local cache, skipping it's build..\n")

        self.create_dirs()
        return self.get_container_cmd

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        # navigate to root directory and clean image from host machine
        os.chdir(self._wdir_local)

        if self.clean_image:
            ccmd.launch(f"{self.benv} rmi {self._name_image}")
