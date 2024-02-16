import os
import json
import shutil
import itertools
from pathlib import Path
from pydantic import BaseModel

import tools.cleaning as cm
import tools.messages as msg
import tools.commands as ccmd
import tools.fileoperations as fo

from modules.kernel_builder import KernelBuilder
from modules.assets_collector import AssetsCollector

from configs.directory_config import DirectoryConfig as dcfg


class BundleCreator(BaseModel):
    """Bundle kernel + asset artifacts.
    
    :param base: Kernel source base.
    :param lkv: Linux kernel version.
    :param package_type: Package type.
    :param ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    lkv: str
    package_type: str
    ksu: bool

    def run(self) -> None:
        os.chdir(dcfg.root)
        # determine the bundle type and process it
        match self.package_type:
            case "slim" | "full":
                self._build_kernel(self.base)
                # "full" chroot is hardcoded here
                self._collect_assets(self.base, "full")
                # make a unified "bundle" directory with both .zips
                bdir = dcfg.bundle
                kdir = dcfg.kernel
                adir = dcfg.assets
                # clean up
                if bdir in os.listdir():
                    contents = Path(bdir).glob("*")
                    for f in contents:
                        os.remove(f)
                else:
                    os.mkdir(bdir)
                # copy kernel
                kfn = "".join(os.listdir(kdir))
                shutil.copy(
                    dcfg.root / kdir / kfn,
                    dcfg.root / bdir / kfn
                )
                # move the assets
                for afn in os.listdir(adir):
                    # here, because of their size assets are moved and not copied
                    shutil.move(
                        dcfg.root / adir / afn,
                        dcfg.root / bdir / afn
                    )
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
                    self._build_kernel(opset[0])
                    self._build_kernel(opset[0], True)
                    self._conan_sources()
                    self._collect_assets(opset[0], opset[1])
                    self._conan_package(opset, reference)
                # upload packages
                if os.getenv("CONAN_UPLOAD_CUSTOM") == "1":
                    self._conan_upload(reference)
        # navigate back to root directory
        os.chdir(dcfg.root)

    def _build_kernel(self, rom_name: str, clean_only: bool = False) -> None:
        """Build the kernel.

        :param rom_name: Name of the ROM.
        :param clean_only: Append an argument to just clean the kernel directory.
        """
        if not Path(dcfg.kernel).is_dir() or clean_only is True:
            KernelBuilder(
                codename = self.codename,
                base = rom_name,
                lkv = self.lkv,
                clean_kernel = clean_only,
                ksu = self.ksu,
            ).run()

    @property
    def _rom_only_flag(self) -> str:
        """Determine the value of the --rom-only flag."""
        return True if "full" not in self.package_type else False

    def _collect_assets(self, rom_name: str, chroot: str) -> None:
        """Collect assets.

        :param rom_name: Name of the ROM.
        :param chroot: Type of chroot.
        """
        AssetsCollector(
            codename = self.codename,
            base = rom_name,
            chroot = chroot,
            clean_assets = True,
            rom_only = self._rom_only_flag,
            ksu = self.ksu,
        ).run()

    def _conan_sources(self) -> None:
        """Prepare sources for rebuildable Conan packages."""
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
    def _conan_options(json_file: str) -> dict:
        """Read Conan options from a JSON file.

        :param json_file: Name of the JSON file to read data from.
        """
        with open(json_file) as f:
            json_data = json.load(f)
        return json_data

    def _conan_package(self, options: list[str], reference: str) -> None:
        """Create the Conan package.

        :param options: Conan options.
        :param reference: Conan reference.
        """
        cmd = f"conan export-pkg . {reference}"
        for option_value in options:
            # not the best solution, but will work temporarily for 'rom' and 'chroot' options
            option_name = "rom" if not any(c.isalpha() for c in option_value) else "chroot"
            cmd += f" -o {option_name}={option_value}"
        # add codename as an option separately
        cmd += f" -o codename={self.codename}"
        ccmd.launch(cmd)

    @staticmethod
    def _conan_upload(reference: str) -> None:
        """Upload Conan component to the remote.

        :param reference: Conan reference.
        """
        # configure Conan client and upload packages
        url = "https://gitlab.com/api/v4/projects/40803264/packages/conan"
        alias = "zero-kernel-conan"
        cmd = f"conan remote add {alias} {url} && "\
              f"conan user -p {os.getenv('CONAN_PASSWORD')} -r {alias} {os.getenv('CONAN_LOGIN_USERNAME')} && "\
              f"conan upload -f {reference} -r {alias}"
        ccmd.launch(cmd)
