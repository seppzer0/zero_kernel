import os
import json
import shutil
import itertools
from pathlib import Path

import tools.cleaning as cm
import tools.messages as msg
import tools.commands as ccmd
import tools.fileoperations as fo

from models.kernel import KernelBuilder
from models.assets import AssetCollector

from configs import Config as cfg


class BundleCreator:
    """Bundle kernel + asset artifacts."""

    _root: Path = cfg.DIR_ROOT

    def __init__(
            self,
            codename: str,
            rom: str,
            package_type: str,
            ksu: bool
        ) -> None:
        self._codename = codename
        self._rom = rom
        self._package_type = package_type
        self._ksu = ksu

    def run(self) -> None:
        os.chdir(self._root)
        # determine the bundle type and process it
        match self._package_type:
            case "slim" | "full":
                self._build_kernel(self._rom)
                # "full" chroot is hardcoded here
                self._collect_assets(self._rom, "full")
                # make a unified "bundle" directory with both .zips
                bdir = cfg.DIR_BUNDLE
                kdir = cfg.DIR_KERNEL
                adir = cfg.DIR_ASSETS
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
                    self._root / kdir / kfn,
                    self._root / bdir / kfn
                )
                # copy the assets
                for afn in os.listdir(adir):
                    shutil.copy(
                        self._root / adir / afn,
                        self._root / bdir / afn
                    )
            case "conan":
                # form Conan reference
                name = "zero_kernel"
                version = os.getenv("KVERSION")
                user = self._codename
                channel = ""
                if ccmd.launch("git branch --show-current", get_output=True) == "main":
                    channel = "stable"
                else:
                    channel = "testing"
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
        os.chdir(self._root)

    def _build_kernel(self, rom_name: str, clean_only: bool = False) -> None:
        """Build the kernel.

        :param rom_name: Name of the ROM.
        :param clean_only: Append an argument to just clean the kernel directory.
        """
        if not Path(cfg.DIR_KERNEL).is_dir() or clean_only is True:
            KernelBuilder(
                codename = self._codename,
                rom = rom_name,
                clean = clean_only,
                ksu = self._ksu,
            ).run()

    @property
    def _rom_only_flag(self) -> str:
        """Determine the value of the --rom-only flag."""
        return True if "full" not in self._package_type else False

    def _collect_assets(self, rom_name: str, chroot: str) -> None:
        """Collect assets.

        :param rom_name: Name of the ROM.
        :param chroot: Type of chroot.
        """
        AssetCollector(
            codename = self._codename,
            rom = rom_name,
            chroot = chroot,
            clean = True,
            rom_only = self._rom_only_flag,
            ksu = self._ksu,
        ).run()

    def _conan_sources(self) -> None:
        """Prepare sources for rebuildable Conan packages."""
        sourcedir = self._root / "source"
        print("\n", end="")
        msg.note("Copying sources for Conan packaging..")
        cm.remove(str(sourcedir))
        fo.ucopy(
            self._root,
            sourcedir,
            (
                cfg.DIR_KERNEL,
                cfg.DIR_ASSETS,
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
        cmd += f" -o codename={self._codename}"
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
