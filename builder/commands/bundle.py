import os
import json
import shutil
import itertools
from typing import Literal
from pydantic import BaseModel

from builder.core import KernelBuilder, AssetsCollector
from builder.tools import cleaning as cm, commands as ccmd, fileoperations as fo, messages as msg
from builder.configs import DirectoryConfig as dcfg
from builder.managers import ResourceManager
from builder.interfaces import ICommand, IBundleCommand


class BundleCommand(BaseModel, ICommand, IBundleCommand):
    """Command that packages the artifacts produced both
    by 'kernel_builder' and 'assets_collector' core modules.

    :param str base: Kernel source base.
    :param str lkv: Linux kernel version.
    :param str package_type: Package type.
    :param bool ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    lkv: str
    package_type: str
    ksu: bool

    def build_kernel(self, rom_name: str, clean_only: bool = False) -> None:
        if not dcfg.kernel.is_dir() or clean_only is True:
            kb = KernelBuilder(
                codename = self.codename,
                base = rom_name,
                lkv = self.lkv,
                clean_kernel = clean_only,
                ksu = self.ksu,
                rmanager=ResourceManager(codename=self.codename, lkv=self.lkv, base=self.base)
            )
            kb.run()

    @property
    def _rom_only_flag(self) -> bool:
        return True if "full" not in self.package_type else False

    def collect_assets(self, rom_name: str, chroot: Literal["full", "minimal"]) -> None:
        ac = AssetsCollector(
            codename = self.codename,
            base = rom_name,
            chroot = chroot,
            clean_assets = True,
            rom_only = self._rom_only_flag,
            ksu = self.ksu,
        )
        ac.run()

    def conan_sources(self) -> None:
        sourcedir = dcfg.root / "source"
        print("\n", end="")
        msg.note("Copying sources for Conan packaging..")
        cm.remove(str(sourcedir))
        fo.ucopy(
            dcfg.root,
            sourcedir,
            (
                dcfg.kernel,
                dcfg.assets,
                "__pycache__",
                ".vscode",
                "source",
                "localversion",
                "conanfile.py",
            )
        )
        msg.done("Done!")

    @staticmethod
    def conan_options(json_file: str) -> dict:
        with open(json_file, encoding="utf-8") as f:
            json_data = json.load(f)
        return json_data

    def conan_package(self, options: tuple[str, ...], reference: str) -> None:
        cmd = f"conan export-pkg . {reference}"
        for option_value in options:
            # not the best solution, but will work temporarily for 'rom' and 'chroot' options
            option_name = "rom" if not any(c.isalpha() for c in option_value) else "chroot"
            cmd += f" -o {option_name}={option_value}"
        # add codename as an option separately
        cmd += f" -o codename={self.codename}"
        ccmd.launch(cmd)

    @staticmethod
    def conan_upload(reference: str) -> None:
        # configure Conan client and upload packages
        url = "https://gitlab.com/api/v4/projects/40803264/packages/conan"
        alias = "zero-kernel-conan"
        cmd = f"conan remote add {alias} {url} && "\
              f"conan user -p {os.getenv('CONAN_PASSWORD')} -r {alias} {os.getenv('CONAN_LOGIN_USERNAME')} && "\
              f"conan upload -f {reference} -r {alias}"
        ccmd.launch(cmd)

    def execute(self) -> None:
        os.chdir(dcfg.root)
        # determine the bundle type and process it
        match self.package_type:
            case "slim" | "full":
                self.build_kernel(self.base)
                # "full" chroot is hardcoded here
                self.collect_assets(self.base, "full")
                # clean up
                if dcfg.bundle.is_dir():
                    contents = dcfg.bundle.glob("*")
                    for f in contents:
                        os.remove(f)
                else:
                    os.makedirs(dcfg.bundle)
                # copy kernel
                kfn = "".join(os.listdir(dcfg.kernel))
                shutil.copy(dcfg.kernel / kfn, dcfg.bundle / kfn)
                # move assets (and not copy because they are way too big)
                for afn in os.listdir(dcfg.assets):
                    # here, because of their size assets are moved and not copied
                    shutil.move(dcfg.assets / afn, dcfg.bundle / afn)
            case "conan":
                # form Conan reference
                name = "zero_kernel"
                version = os.getenv("KVERSION")
                user = self.codename
                channel = ""
                if ccmd.launch("git branch --show-current", get_output=True) == "main":
                    channel = "stable"
                else:
                    channel = "testing"
                reference = f"{name}/{version}@{user}/{channel}"
                # form option sets
                chroot = ("minimal", "full")
                option_sets = list(itertools.product([self.base], chroot))
                # build and upload Conan packages
                for opset in option_sets:
                    self.build_kernel(opset[0])
                    self.build_kernel(opset[0], True)
                    self.conan_sources()
                    self.collect_assets(opset[0], opset[1])
                    self.conan_package(opset, reference)
                # upload packages
                if os.getenv("CONAN_UPLOAD_CUSTOM") == "1":
                    self.conan_upload(reference)
        # navigate back to root directory
        os.chdir(dcfg.root)
