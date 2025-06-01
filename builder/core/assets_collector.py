import os
import sys
import logging
from typing import Literal
from pydantic import BaseModel

from builder.tools import Logger, cleaning as cm, fileoperations as fo, banner
from builder.clients import GithubApiClient, LineageOsApiClient, ParanoidAndroidApiClient
from builder.configs import DirectoryConfig as dcfg
from builder.interfaces import IAssetsCollector


log = logging.getLogger("ZeroKernelLogger")


class AssetsCollector(BaseModel, IAssetsCollector):
    """Assets collector.

    :param str codename: Device codename.
    :param str base: Kernel source base.
    :param Literal["full","minimal"] chroot: Chroot type.
    :param bool rom_only: Flag indicating ROM-only asset collection.
    :param bool ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    chroot: Literal["full", "minimal"]
    clean_assets: bool
    rom_only: bool
    ksu: bool

    @property
    def rom_collector_dto(self) -> LineageOsApiClient | ParanoidAndroidApiClient | None:
        match self.base:
            case "los":
                return LineageOsApiClient(codename=self.codename, rom_only=self.rom_only)
            case "pa":
                return ParanoidAndroidApiClient(codename=self.codename, rom_only=self.rom_only)
            case "x" | "aosp":
                # selected kernel base is ROM-universal, no specific ROM image will be collected
                return None

    @property
    def assets(self) -> list:
        # define Disable_Dm-Verity_ForceEncrypt and SU manager
        dfd = GithubApiClient(project="seppzer0/Disable_Dm-Verity_ForceEncrypt")
        su_manager = "tiann/KernelSU" if self.ksu else "topjohnwu/Magisk"

        # process the "ROM-only" download for non-universal kernel bases
        if self.rom_only:
            if not self.rom_collector_dto:
                return [dfd,]
            else:
                # add DFD alongside the ROM
                print("\n", end="")
                log.info("ROM-only asset collection specified")
                return [self.rom_collector_dto.run(), dfd]

        # process the full download
        else:
            assets = [
                # Disable_Dm-Verity_ForceEncrypt
                dfd,
                # files from GitHub projects
                GithubApiClient(
                    project=su_manager,
                    file_filter=".apk"
                ),
                GithubApiClient(
                    project="klausw/hackerskeyboard",
                    file_filter=".apk"
                ),
                GithubApiClient(
                    project="aleksey-saenko/TTLChanger",
                    file_filter=".apk"
                ),
                GithubApiClient(
                    project="ukanth/afwall",
                    file_filter=".apk"
                ),
                GithubApiClient(
                    project="emanuele-f/PCAPdroid",
                    file_filter=".apk"
                ),
                GithubApiClient(
                    project="nfcgate/nfcgate",
                    file_filter=".apk"
                ),
                # files from direct URLs
                "https://store.nethunter.com/NetHunter.apk",
                "https://store.nethunter.com/NetHunterKeX.apk",
                "https://store.nethunter.com/NetHunterStore.apk",
                "https://store.nethunter.com/NetHunterTerminal.apk",
                "https://sourceforge.net/projects/op5-5t/files/Android-12/TWRP/twrp-3.7.0_12-5-dyn-cheeseburger_dumpling.img/download",
                "https://kali.download/nethunter-images/current/rootfs/kali-nethunter-rootfs-{}-arm64.tar.xz".format(self.chroot),
                "https://github.com/mozilla-mobile/firefox-android/releases/download/fenix-v117.1.0/fenix-117.1.0-arm64-v8a.apk",
                "https://f-droid.org/F-Droid.apk",
            ]

            # add ROM if kernel base is not universal
            if self.rom_collector_dto:
                assets.append(self.rom_collector_dto.run()) # type: ignore

            return assets

        return None

    def _check(self) -> None:
        os.chdir(dcfg.root)

        # directory check
        if not dcfg.assets.is_dir():
            os.makedirs(dcfg.assets)
        else:
            if len(os.listdir(dcfg.assets)) != 0:
                cmsg = f'[ ? ] Found an existing "{dcfg.assets.name}" folder, clean it? [Y/n]: '
                ans = input(cmsg).lower() if not self.clean_assets else "y"

                match ans:
                    case "y":
                        log.warning("Cleaning 'assets' directory..")
                        os.chdir(dcfg.assets)
                        cm.remove("./*")
                        os.chdir(dcfg.root)
                        log.info("Done!")
                    case "n":
                        log.warning("Cancelling asset download.")
                    case _:
                        log.error("Invalid option selected.")
                        sys.exit(1)

        print("\n", end="")

    def run(self) -> None:
        banner.print_banner("zero asset collector")

        os.chdir(dcfg.root)
        self._check()
        os.chdir(dcfg.assets)
        # NOTE: call "self.assets" only once!
        assets = self.assets

        if isinstance(assets, list) or isinstance(assets, tuple):
            for e in assets:
                if isinstance(e, GithubApiClient):
                    e.run()
                else:
                    fo.download(e)

        print("\n", end="")
        log.info("Assets collected!")
        os.chdir(dcfg.root)
