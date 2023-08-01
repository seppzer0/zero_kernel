import os
import json
from pathlib import Path
from typing import Optional

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg
import wrapper.tools.fileoperations as fo

from wrapper.clients import GitHubApi, LineageOsApi, ParanoidAndroidApi


class AssetCollector:
    """Asset collector."""

    def __init__(
        self,
        codename: str,
        rom: str,
        chroot: str,
        clean: bool,
        rom_only: bool,
        extra_assets: Optional[bool] = False,
        kernelsu: Optional[bool] = False
    ) -> None:
        self._codename = codename
        self._rom = rom
        self._chroot = chroot
        self._extra_assets = extra_assets
        self._clean = clean
        self._rom_only = rom_only
        self._kernelsu = kernelsu

    @property
    def _workdir(self):
        return Path(os.getenv("ROOTPATH"))

    @property
    def _assetdir(self):
        return Path(self._workdir, "assets")

    def run(self) -> None:
        msg.banner("s0nh Asset Collector")
        os.chdir(self._workdir)
        self._check()
        os.chdir(self._assetdir)
        # process the ROM-only download
        if self._rom_only:
            fo.download(LineageOsApi(self._codename, self._rom_only).run())
            print("\n", end="")
            msg.done("ROM-only asset collection complete!")
        else:
            # determine which SU manager is required
            su_manager = "tiann/KernelSU" if self._kernelsu else "topjohnwu/Magisk"
            # same with the collected ROM
            rom_collector_dto = ""
            if self._rom == "lineageos":
                rom_collector_dto = LineageOsApi(self._codename, self._rom_only)
            else:
                rom_collector_dto = ParanoidAndroidApi(self._codename, self._rom_only)
            assets = [
                rom_collector_dto.run(),
                GitHubApi(project=su_manager, assetdir=self._assetdir, file_filter=".apk").run(),
                "https://store.nethunter.com/NetHunter.apk",
                "https://store.nethunter.com/NetHunterKeX.apk",
                "https://store.nethunter.com/NetHunterStore.apk",
                "https://store.nethunter.com/NetHunterTerminal.apk",
                "https://eu.dl.twrp.me/cheeseburger_dumpling/twrp-3.7.0_12-1-cheeseburger_dumpling.img",
                "https://kali.download/nethunter-images/current/rootfs/kalifs-arm64-{}.tar.xz".format(self._chroot),
                #"https://sourceforge.net/projects/multi-function-patch/files/DFE-NEO/DFE-NEO-1.5.3.015-BETA.zip",
            ]
            # read extra assets from JSON file
            if self._extra_assets:
                extra_json = Path(self._workdir, self._extra_assets)
                if extra_json.is_file():
                    print("\n", end="")
                    msg.note("Applying extra assets..")
                    with open(extra_json) as f:
                        data = json.load(f)
                        # validate the input JSON
                        rootkeys = ("github", "local", "other")
                        if not all(le in data.keys() for le in rootkeys):
                            msg.error(
                                "Incorrect JSON syntax detected."
                                "Allowed keys: 'github', 'local', 'other' ."
                            )
                        # append extra asset data
                        for k in rootkeys:
                            if data[k]:
                                for e in data[k]:
                                    if k == "github":
                                        assets.append(GitHubApi(e))
                                    else:
                                        assets.append(e)
                    msg.done("Extra assets added!")
                    print("\n", end="")
            # collect all the specified assets into single directory
            nhpatch = "nhpatch.sh"
            fo.ucopy(
                Path(self._workdir, "modifications", nhpatch),
                Path(self._assetdir, nhpatch)
            )
            for e in assets:
                if e:
                    fo.download(e)
            print("\n", end="")
            msg.done("Assets collected!")
        os.chdir(self._workdir)

    def _check(self) -> None:
        """Initiate some checks before execution."""
        os.chdir(self._workdir)
        # directory validation
        if not self._assetdir.is_dir():
            os.mkdir(self._assetdir)
        else:
            if len(os.listdir(self._assetdir)) != 0:
                msg.note(f"Found an existing \"{self._assetdir.name}\" folder, clean it?")
                ans = input("[Y/n]: ").lower() if not self._clean else "y"
                if ans == "y":
                    msg.note("Cleaning 'assets' directory..")
                    cm.remove(str(self._assetdir))
                    os.mkdir(self._assetdir)
                    msg.done("Done!")
                elif ans == "n":
                    msg.cancel("Cancelling asset download.")
                else:
                    msg.error("Invalid option selected.")
        print("\n", end="")
