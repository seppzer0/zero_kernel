import os
import sys
import glob
import json
import shutil
import argparse
import itertools
import subprocess
from typing import List

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import cleaning as cm
import commands as ccmd
import fileoperations as fo
import messages as msg

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "models"))
from kernel import KernelBuilder
from assets import AssetCollector


class BundleCreator:
    """Bundle kernel + asset artifacts."""

    def __init__(self, codename: str, losversion: str, package_type: str):
        self._codename = codename
        self._losversion = losversion
        self._package_type = package_type
        self._workdir = os.getenv("ROOTPATH")
        self._exec()

    def __exit__(self):
        os.chdir(self._workdir)

    def _exec(self) -> None:
        os.chdir(self._workdir)
        # get either a "kernel+ROM" or "kernel+assets=Conan" bundle (the latter is bigger)
        if self._package_type == "generic-slim":
            self._build_kernel(self._losversion)
            self._collect_assets(self._losversion, "minimal")
            # make a unified "release-slim" directory with both .zips
            reldir_slim = "release-slim"
            kdir = "kernel"
            adir = "assets"
            # clean up
            if reldir_slim in os.listdir():
                contents = glob.glob(os.path.join(reldir_slim, "*"))
                for f in contents:
                    os.remove(f)
            else:
                os.mkdir(reldir_slim)
            # copy kernel
            kfn = "".join(os.listdir(kdir))
            shutil.copy(os.path.join(self._workdir, kdir, kfn),
                        os.path.join(self._workdir, reldir_slim, kfn))
            # copy the asset (ROM)
            afn = "".join(os.listdir(adir))
            shutil.copy(os.path.join(self._workdir, adir, afn),
                        os.path.join(self._workdir, reldir_slim, afn))
        elif self._package_type == "conan":
            # form Conan reference
            name = os.getenv("KNAME")
            version = os.getenv("KVERSION")
            user = self._codename
            channel = "stable" if ccmd.launch("git branch --show-current", get_output=True) == "main" else "testing"
            reference = f"{name}/{version}@{user}/{channel}"
            # form option sets
            chroot = ["minimal", "full"]
            option_sets = list(itertools.product([self._losversion], chroot))
            # build and upload Conan packages
            fo.ucopy(os.path.join(self._workdir, "conan"), self._workdir)
            for opset in option_sets:
                self._build_kernel(opset[0])
                self._build_kernel(opset[0], True)
                self._conan_sources()
                self._collect_assets(opset[0], opset[1])
                self._conan_package(opset, reference)
            # upload packages
            if os.getenv("self._CONAN_UPLOAD_CUSTOM") == "1":
                self._conan_upload(reference)

    def _build_kernel(self, losver: str, clean_only: bool = False) -> None:
        """Build the kernel.

        :param str losver: LineageOS version.
        :param bool clean_only: Append an argument to only clean kernel directory.
        """
        if not os.path.isdir("kernel") or clean_only is True:
            KernelBuilder(self._codename, losver, clean_only)

    def _collect_assets(self, losver: str, chroot: str) -> None:
        """Collect assets.

        :param str losver: LineageOS version.
        :param str chroot: Type of chroot.
        """
        AssetCollector(self._codename, losver, chroot, True, True)

    def _conan_sources(self) -> None:
        """Prepare sources for rebuildable Conan packages."""
        sourcedir = os.path.join(self._workdir, "source")
        print("\n", end="")
        msg.note("Copying sources for Conan packaging..")
        cm.remove(sourcedir, allow_errors=True)
        fo.ucopy(self._workdir, sourcedir, ("__pycache__",
                                            ".vscode",
                                            "source",
                                            "kernel",
                                            "localversion",
                                            "assets",
                                            "conanfile.py"))
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

    @staticmethod
    def _conan_package(options: List[str], reference: str) -> None:
        """Create the Conan package.

        :param list options: Conan options.
        :param str reference: Conan reference.
        """
        cmd = f"conan export-pkg . {reference}"
        for option_value in options:
            # not the best solution, but will work temporarily for 'losversion' and 'chroot' options
            option_name = "losversion" if not any(c.isalpha() for c in option_value) else "chroot"
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
