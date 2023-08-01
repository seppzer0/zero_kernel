import os
import json
import shutil
import itertools
from typing import List
from pathlib import Path

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg
import wrapper.tools.commands as ccmd
import wrapper.tools.fileoperations as fo

from wrapper.models.kernel import KernelBuilder
from wrapper.models.assets import AssetCollector


class BundleCreator:
    """Bundle kernel + asset artifacts."""

    def __init__(
            self,
            codename: str,
            rom: str,
            package_type: str,
            kernelsu: bool
        ) -> None:
        self._codename = codename
        self._rom = rom
        self._package_type = package_type
        self._kernelsu = kernelsu

    @property
    def _workdir(self) -> os.PathLike:
        return Path(os.getenv("ROOTPATH"))

    def run(self) -> None:
        os.chdir(self._workdir)
        # get either a "kernel+ROM" or "kernel+assets=Conan" or "kernel+assets" bundle
        if self._package_type in ("slim", "full"):
            self._build_kernel(self._rom)
            self._collect_assets(self._rom, "minimal")
            # make a unified "release-*" directory with both .zips
            reldir_generic = f"release-{self._package_type}"
            kdir = "kernel"
            adir = "assets"
            # clean up
            if reldir_generic in os.listdir():
                contents = Path(reldir_generic).glob("*")
                for f in contents:
                    os.remove(f)
            else:
                os.mkdir(reldir_generic)
            # copy kernel
            kfn = "".join(os.listdir(kdir))
            shutil.copy(
                self._workdir / kdir / kfn,
                self._workdir / reldir_generic / kfn
            )
            # copy the assets
            for afn in os.listdir(adir):
                shutil.copy(
                    self._workdir / adir / afn,
                    self._workdir / reldir_generic / afn
                )
        elif self._package_type == "conan":
            # form Conan reference
            name = "s0nh"
            version = os.getenv("KVERSION")
            user = self._codename
            channel = "stable" if ccmd.launch("git branch --show-current", get_output=True) == "main" else "testing"
            reference = f"{name}/{version}@{user}/{channel}"
            # form option sets
            chroot = ("minimal", "full")
            option_sets = list(itertools.product([self._rom], chroot))
            # build and upload Conan packages
            for opset in option_sets:
                self._build_kernel(opset[0])
                self._build_kernel(opset[0], True)
                self._conan_sources()
                self._collect_assets(opset[0], opset[1])
                self._conan_package(opset, reference)
            # upload packages
            if os.getenv("CONAN_UPLOAD_CUSTOM") == "1":
                self._conan_upload(reference)
        # navigate back to root directory
        os.chdir(self._workdir)

    def _build_kernel(self, rom_name: str, clean_only: bool = False) -> None:
        """Build the kernel.

        :param str rom_name: LineageOS version.
        :param bool clean_only: Append an argument to only clean kernel directory.
        """
        if not Path("kernel").is_dir() or clean_only is True:
            KernelBuilder(
                codename = self._codename,
                rom = rom_name,
                clean = clean_only,
                kernelsu = self._kernelsu,
            ).run()

    @property
    def _rom_only_flag(self) -> str:
        """Determine the value of the --rom-only flag."""
        return True if "full" not in self._package_type else False

    def _collect_assets(self, rom_name: str, chroot: str) -> None:
        """Collect assets.

        :param str rom_name: LineageOS version.
        :param str chroot: Type of chroot.
        """
        AssetCollector(
            codename = self._codename,
            rom = rom_name,
            chroot = chroot,
            clean = True,
            rom_only = self._rom_only_flag,
            kernelsu = self._kernelsu,
        ).run()

    def _conan_sources(self) -> None:
        """Prepare sources for rebuildable Conan packages."""
        sourcedir = self._workdir / "source"
        print("\n", end="")
        msg.note("Copying sources for Conan packaging..")
        cm.remove(str(sourcedir), allow_errors=True)
        fo.ucopy(
            self._workdir,
            sourcedir,
            (
                "__pycache__",
                ".vscode",
                "source",
                "kernel",
                "localversion",
                "assets",
                "conanfile.py",
            )
        )
        msg.done("Done!")

    @staticmethod
    def _conan_options(json_file: str) -> dict:
        """Read Conan options from a JSON file.

        :param str json_file: Name of the JSON file to read data from.
        :rtype: dict
        """
        with open(json_file) as f:
            json_data = json.load(f)
        return json_data

    def _conan_package(self, options: List[str], reference: str) -> None:
        """Create the Conan package.

        :param list options: Conan options.
        :param str reference: Conan reference.
        """
        cmd = f"conan export-pkg . {reference}"
        for option_value in options:
            # not the best solution, but will work temporarily for 'rom' and 'chroot' options
            option_name = "rom" if not any(c.isalpha() for c in option_value) else "chroot"
            cmd += f" -o {option_name}={option_value}"
        # add codename as an option separately
        cmd += f" -o codename={self._codename}"
        ccmd.launch(cmd)

    @staticmethod
    def _conan_upload(reference: str) -> None:
        """Upload Conan component to the remote.

        :param str reference: Conan reference.
        """
        # configure Conan client and upload packages
        url = "https://gitlab.com/api/v4/projects/40803264/packages/conan"
        alias = "s0nh-conan"
        cmd = f"conan remote add {alias} {url} && "\
              f"conan user -p {os.getenv('CONAN_PASSWORD')} -r {alias} {os.getenv('CONAN_LOGIN_USERNAME')} && "\
              f"conan upload -f {reference} -r {alias}"
        ccmd.launch(cmd)
