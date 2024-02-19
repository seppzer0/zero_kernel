import os
from pathlib import Path
from pydantic import BaseModel

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg
import wrapper.tools.fileoperations as fo

from wrapper.clients import GitHubApi, LineageOsApi, ParanoidAndroidApi

from wrapper.configs.directory_config import DirectoryConfig as dcfg

from wrapper.modules.interfaces import IModuleExecutor


class AssetsCollector(BaseModel, IModuleExecutor):
    """Assets collector.

    :param codename: Device codename.
    :param base: Kernel source base.
    :param chroot: Chroot type.
    :param rom_only: Flag indicating ROM-only asset collection.
    :param ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    chroot: str
    clean_assets: bool
    rom_only: bool
    ksu: bool

    def run(self) -> None:
        os.chdir(dcfg.root)
        msg.banner("zero asset collector")
        self._check()
        os.chdir(dcfg.assets)
        # determine which SU manager and ROM are required
        su_manager = "tiann/KernelSU" if self.ksu else "topjohnwu/Magisk"
        rom_collector_dto = ""
        match self.base:
            case "los":
                rom_collector_dto = LineageOsApi(codename=self.codename)
            case "pa":
                rom_collector_dto = ParanoidAndroidApi(codename=self.codename)
            case "x" | "aosp":
                msg.note("Selected kernel base is ROM-universal, no specific ROM image will be collected")
        # process the "ROM-only" download for non-universal kernel bases
        if self.rom_only:
            if self.base in ("x", "aosp"):
                msg.cancel("Cancelling assets collection")
            else:
                fo.download(rom_collector_dto.run())
                print("\n", end="")
                msg.done("ROM-only asset collection complete!")
        # process the non-"RON-only" download
        else:
            assets = [
                # files from GitHub projects
                GitHubApi(
                    project=su_manager,
                    assetdir=dcfg.assets,
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="seppzer0/Disable_Dm-Verity_ForceEncrypt",
                    assetdir=dcfg.assets
                ).run(),
                GitHubApi(
                    project="klausw/hackerskeyboard",
                    assetdir=dcfg.assets,
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="aleksey-saenko/TTLChanger",
                    assetdir=dcfg.assets,
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="ukanth/afwall",
                    assetdir=dcfg.assets,
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="emanuele-f/PCAPdroid",
                    assetdir=dcfg.assets,
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="nfcgate/nfcgate",
                    assetdir=dcfg.assets,
                    file_filter=".apk"
                ).run(),
                # files from direct URLs
                "https://store.nethunter.com/NetHunter.apk",
                "https://store.nethunter.com/NetHunterKeX.apk",
                "https://store.nethunter.com/NetHunterStore.apk",
                "https://store.nethunter.com/NetHunterTerminal.apk",
                "https://sourceforge.net/projects/op5-5t/files/Android-12/TWRP/twrp-3.7.0_12-5-dyn-cheeseburger_dumpling.img/download",
                "https://kali.download/nethunter-images/current/rootfs/kalifs-arm64-{}.tar.xz".format(self.chroot),
                "https://github.com/mozilla-mobile/firefox-android/releases/download/fenix-v117.1.0/fenix-117.1.0-arm64-v8a.apk",
                "https://f-droid.org/F-Droid.apk",
            ]
            # finally, add ROM into assets list if kernel base is not universal
            if self.base not in ("x", "aosp"):
                assets.append(rom_collector_dto.run())
            # collect all the specified assets into single directory
            nhpatch = "nhpatch.sh"
            fo.ucopy(
                Path(dcfg.root, "modifications", nhpatch),
                Path(dcfg.assets, nhpatch)
            )
            for e in assets:
                if e:
                    fo.download(e)
            print("\n", end="")
            msg.done("Assets collected!")
        os.chdir(dcfg.root)

    def _check(self) -> None:
        """Initiate some checks before execution."""
        os.chdir(dcfg.root)
        # directory check
        if not dcfg.assets.is_dir():
            os.mkdir(dcfg.assets)
        else:
            if len(os.listdir(dcfg.assets)) != 0:
                cmsg = f'[ ? ] Found an existing "{dcfg.assets.name}" folder, clean it? [Y/n]: '
                ans = input(cmsg).lower() if not self.clean_assets else "y"
                match ans:
                    case "y":
                        msg.note("Cleaning 'assets' directory..")
                        os.chdir(dcfg.assets)
                        cm.remove("./*")
                        os.chdir(dcfg.root)
                        msg.done("Done!")
                    case "n":
                        msg.cancel("Cancelling asset download.")
                    case _:
                        msg.error("Invalid option selected.")
        print("\n", end="")
