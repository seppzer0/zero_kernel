import os
import sys
import shutil
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import commands as ccmd
import messages as msg


class ContainerEngine:
    """Use containers (Docker/Podman) for the build."""

    def __init__(self, config: dict):
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
        self._image_name = "s0nh-docker-image"
        self._container_name = "s0nh-docker-container"
        self._docker_workdir = "s0nh_build"
        self._local_workdir = os.getenv("ROOTPATH")
        self._initial_dir = os.getcwd()
        self._exec()

    def _exec(self) -> None:
        os.chdir(os.getenv("ROOTPATH"))
        # force enable Docker Buildkit create Docker image
        if self._buildenv == "docker":
            os.environ["DOCKER_BUILDKIT"] = "1"
        cmd = f"{self._buildenv} build . -f {os.path.join(self._local_workdir, 'docker', 'Dockerfile')} -t {self._image_name}"
        ccmd.launch(cmd)
        # prepare launch command
        base_cmd = f"python3 {os.path.join('wrapper', 'engines', 'bridge.py')}"
        arguments = {
            "--build-module": self._build_module,
            "--codename": self._codename,
            "--losversion": self._losversion,
            "--chroot": self._chroot,
            "--package-type": self._package_type,
            "--rom-only": self._rom_only,
            "--extra-assets": self._extra_assets
        }
        for arg, value in arguments.items():
            if value not in [None, False]:
                base_cmd += f" {arg}={value}"
        cmd = f'{self._buildenv} run -i --rm -e ROOTPATH=/{self._docker_workdir} -w /{self._docker_workdir} {self._image_name} /bin/bash -c "{base_cmd}"'
        # mount directories
        if self._build_module == "kernel":
            kdir = "kernel"
            if not os.path.isdir(kdir):
                os.mkdir(kdir)
            cmd = cmd.replace(f'-w /{self._docker_workdir}',
                              f'-w /{self._docker_workdir} '\
                              f'-v {os.getenv("ROOTPATH")}/{kdir}:/{self._docker_workdir}/{kdir}')
        elif self._build_module == "assets":
            assetsdir = "assets"
            if not os.path.isdir(assetsdir):
                os.mkdir(assetsdir)
            cmd = cmd.replace(f'-w /{self._docker_workdir}',
                              f'-w /{self._docker_workdir} '\
                              f'-v {os.getenv("ROOTPATH")}/{assetsdir}:/{self._docker_workdir}/{assetsdir}')
        if self._build_module == "bundle":
            if self._package_type == "generic-slim":
                # mount directory with "slim" release artifacts
                reldir_slim = "release-slim"
                shutil.rmtree(reldir_slim, ignore_errors=True)
                os.mkdir(reldir_slim)
                cmd = cmd.replace(f'-w /{self._docker_workdir}',
                                  f'-w /{self._docker_workdir} '\
                                  f'-v {os.getenv("ROOTPATH")}/{reldir_slim}:/{self._docker_workdir}/{reldir_slim}')
                cmd = cmd.replace(base_cmd, base_cmd + f" && chmod 777 -R /{os.path.join(self._docker_workdir, reldir_slim)}")
            elif self._package_type == "conan":
                if args.conan_upload:
                    cmd = cmd.replace(f'-w /{self._docker_workdir}',
                                      f'-e CONAN_UPLOAD_CUSTOM=1 -w /{self._docker_workdir}')
                cmd = cmd.replace(base_cmd, base_cmd + " && chmod 777 -R /root/.conan")
                # determine the path to local Conan cache and check if it exists
                conan_cache_dir = ""
                if os.getenv("CONAN_USER_HOME"):
                    conan_cache_dir = os.getenv("CONAN_USER_HOME")
                else:
                    conan_cache_dir = os.path.join(os.getenv("HOME"), ".conan")
                if os.path.isdir(conan_cache_dir):
                    cmd = cmd.replace(f'-w /{self._docker_workdir}',
                                      f'-w /{self._docker_workdir} -v {conan_cache_dir}:/"/root/.conan"')
                else:
                    msg.error("Could not find Conan local cache on the host machine.")
        ccmd.launch(cmd)
        os.chdir(self._initial_dir)

    def __exit__():
        if self._clean_image:
            ccmd(f"{self._buildenv} rmi {self._image_name}")
