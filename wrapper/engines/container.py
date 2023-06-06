import os
import shutil
from pathlib import Path

import wrapper.tools.commands as ccmd
import wrapper.tools.messages as msg


class ContainerEngine:
    """Use containers (Docker/Podman) for the build."""

    def __init__(self, config: dict) -> None:
        self._buildenv = config.get("buildenv")
        self._build_module = config.get("build_module")
        self._codename = config.get("codename")
        self._losversion = config.get("losversion")
        self._clean_image = config.get("clean_image", False)
        self._chroot = config.get("chroot", None)
        self._package_type = config.get("package_type", None)
        self._clean_kernel = config.get("clean_kernel", False)
        self._clean_assets = config.get("clean_assets", False)
        self._rom_only = config.get("rom_only", False)
        self._extra_assets = config.get("extra_assets", False)
        self._conan_upload = config.get("conan_upload", False)

    @property
    def _image_name(self) -> str:
        return "s0nh-docker-image"

    @property
    def _container_name(self) -> str:
        return "s0nh-docker-container"

    @property
    def _local_workdir(self) -> os.PathLike:
        return Path(os.getenv("ROOTPATH"))

    @property
    def _docker_workdir(self) -> str:
        return "s0nh_build"

    @property
    def _initial_dir(self) -> os.PathLike:
        return Path.cwd()

    def run(self) -> None:
        os.chdir(self._local_workdir)
        # force enable Docker Buildkit create Docker image
        if self._buildenv == "docker":
            os.environ["DOCKER_BUILDKIT"] = "1"
        cmd = f"{self._buildenv} build . -f {self._local_workdir / 'docker' / 'Dockerfile'} -t {self._image_name}"
        ccmd.launch(cmd)
        # prepare launch command
        base_cmd = f"python3 {Path('wrapper', 'utils', 'bridge.py')}"
        arguments = {
            "--build-module": self._build_module,
            "--codename": self._codename,
            "--losversion": self._losversion,
            "--chroot": self._chroot,
            "--package-type": self._package_type,
            "--rom-only": self._rom_only,
            "--extra-assets": self._extra_assets
        }
        # form a base command that will be launched in container
        for arg, value in arguments.items():
            if value not in [None, False]:
                base_cmd += f" {arg}={value}"
        cmd = f'{self._buildenv} run -i --rm -e ROOTPATH=/{self._docker_workdir} -w /{self._docker_workdir} {self._image_name} /bin/bash -c "{base_cmd}"'
        # mount directories
        if self._build_module == "kernel":
            kdir = Path("kernel")
            if not kdir.is_dir():
                os.mkdir(kdir)
            cmd = cmd.replace(
                f'-w /{self._docker_workdir}',
                f'-w /{self._docker_workdir} '\
                f'-v {os.getenv("ROOTPATH")}/{kdir}:/{self._docker_workdir}/{kdir}'
            )
        elif self._build_module == "assets":
            assetsdir = Path("assets")
            if not assetsdir.is_dir():
                os.mkdir(assetsdir)
            cmd = cmd.replace(
                f'-w /{self._docker_workdir}',
                f'-w /{self._docker_workdir} '\
                f'-v {os.getenv("ROOTPATH")}/{assetsdir}:/{self._docker_workdir}/{assetsdir}'
            )
        if self._build_module == "bundle":
            if self._package_type == "generic-slim":
                # mount directory with "slim" release artifacts
                reldir_slim = "release-slim"
                shutil.rmtree(reldir_slim, ignore_errors=True)
                os.mkdir(reldir_slim)
                cmd = cmd.replace(
                    f'-w /{self._docker_workdir}',
                    f'-w /{self._docker_workdir} '\
                    f'-v {os.getenv("ROOTPATH")}/{reldir_slim}:/{self._docker_workdir}/{reldir_slim}'
                )
                cmd = cmd.replace(base_cmd, base_cmd + f" && chmod 777 -R /{Path(self._docker_workdir, reldir_slim)}")
            elif self._package_type == "conan":
                if self._conan_upload:
                    cmd = cmd.replace(f'-w /{self._docker_workdir}',
                                      f'-e CONAN_UPLOAD_CUSTOM=1 -w /{self._docker_workdir}')
                cmd = cmd.replace(base_cmd, base_cmd + " && chmod 777 -R /root/.conan")
                # determine the path to local Conan cache and check if it exists
                cache_dir = Path(os.getenv("CONAN_USER_HOME")) if os.getenv("CONAN_USER_HOME") else Path(os.getenv("HOME"), ".conan")
                if cache_dir.is_dir():
                    cmd = cmd.replace(
                        f'-w /{self._docker_workdir}',
                        f'-w /{self._docker_workdir} -v {cache_dir}:/"/root/.conan"'
                    )
                else:
                    msg.error("Could not find Conan local cache on the host machine.")
        ccmd.launch(cmd)
        # navigate to root directory and clean image from host machine
        os.chdir(self._initial_dir)
        if self._clean_image:
            ccmd(f"{self._buildenv} rmi {self._image_name}")
