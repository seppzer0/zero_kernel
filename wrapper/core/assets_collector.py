import os
from pydantic import BaseModel

from wrapper.tools import cleaning as cm, fileoperations as fo, messages as msg
from wrapper.clients import GitHubApi, LineageOsApi, ParanoidAndroidApi
from wrapper.configs import DirectoryConfig as dcfg
from wrapper.interfaces import IAssetsCollector


class AssetsCollector(BaseModel, IAssetsCollector):
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

    @property
    def rom_collector_dto(self) -> LineageOsApi | ParanoidAndroidApi | None:
        rom_collector_dto = ""
        match self.base:
            case "los":
                rom_collector_dto = LineageOsApi(codename=self.codename, rom_only=self.rom_only)
            case "pa":
                rom_collector_dto = ParanoidAndroidApi(codename=self.codename, rom_only=self.rom_only)
            case "x" | "aosp":
                msg.note("Selected kernel base is ROM-universal, no specific ROM image will be collected")
        return rom_collector_dto

    @property
    def assets(self) -> tuple[str | None] | list[str | None]:
        # define dm-verity and forceencrypt disabler (DFD) and SU manager
        dfd = GitHubApi(project="seppzer0/Disable_Dm-Verity_ForceEncrypt").run()
        su_manager = "tiann/KernelSU" if self.ksu else "topjohnwu/Magisk"
        # process the "ROM-only" download for non-universal kernel bases
        if self.rom_only:
            if not self.rom_collector_dto:
                msg.cancel("Cancelling ROM-only asset collection")
            else:
                # add DFD alongside the ROM
                assets = (self.rom_collector_dto.run(), dfd)
                print("\n", end="")
                msg.done("ROM-only asset collection complete!")
        # process the non-"RON-only" download
        else:
            assets = [
                # DFD
                dfd,
                # files from GitHub projects
                GitHubApi(
                    project=su_manager,
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="klausw/hackerskeyboard",
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="aleksey-saenko/TTLChanger",
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="ukanth/afwall",
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="emanuele-f/PCAPdroid",
                    file_filter=".apk"
                ).run(),
                GitHubApi(
                    project="nfcgate/nfcgate",
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
            # finally, add ROM (if kernel base is not universal) and DFD into assets list
            if self.rom_collector_dto:
                assets.append(self.rom_collector_dto.run())
        return assets

    def _check(self) -> None:
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

    def run(self) -> None:
        os.chdir(dcfg.root)
        msg.banner("zero asset collector")
        self._check()
        os.chdir(dcfg.assets)
        for e in self.assets:
            if e is not None:
                fo.download(e)
        print("\n", end="")
        msg.done("Assets collected!")
        os.chdir(dcfg.root)
