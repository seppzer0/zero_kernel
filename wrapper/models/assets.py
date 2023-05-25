import io
import os
import sys
import json
import shutil
import argparse
import requests
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import cleaning as cm
import commands as ccmd
import fileoperations as fo
import messages as msg


class AssetCollector:
    """Asset collector."""

    def __init__(self, codename: str, losversion: str, chroot: str, clean: bool, rom_only: bool, extra_assets: Optional[bool] = False):
        self._codename = codename
        self._losversion = losversion
        self._chroot = chroot
        self._extra_assets = extra_assets
        self._clean = clean
        self._rom_only = rom_only
        self._workdir = os.getenv("ROOTPATH")
        self._assetdir = os.path.join(self._workdir, "assets")
        self._exec()

    def __exit__(self):
        os.chdir(self._workdir)

    def _exec(self) -> None:
        msg.banner("s0nh Asset Collector")
        os.chdir(self._workdir)
        self._check()
        os.chdir(self._assetdir)
        # process the ROM-only download
        if self._rom_only:
            fo.download(self._api_rom())
            print("\n", end="")
            msg.done("ROM-only asset collection complete!")
        else:
            assets = [
                self._api_rom(),
                self._api_github("engstk/android_device_oneplus_cheeseburger"),
                self._api_github("topjohnwu/Magisk"),
                self._api_github("Magisk-Modules-Repo/wirelessFirmware"),
                "https://store.nethunter.com/NetHunter.apk",
                "https://store.nethunter.com/NetHunterKeX.apk",
                "https://store.nethunter.com/NetHunterStore.apk",
                "https://store.nethunter.com/NetHunterTerminal.apk",
                "https://store.nethunter.com/repo/org.pocketworkstation.pckeyboard_1041001.apk",
                f"https://kali.download/nethunter-images/current/rootfs/kalifs-arm64-{self._chroot}.tar.xz"
            ]
            # read extra assets from JSON file
            if self._extra_assets:
                extra_json = os.path.join(self._workdir, self._extra_assets)
                if os.path.isfile(extra_json):
                    print("\n", end="")
                    msg.note("Applying extra assets..")
                    with open(extra_json) as f:
                        data = json.load(f)
                        # validate the input JSON
                        rootkeys = ("github", "local", "other")
                        if not all(le in data.keys() for le in rootkeys):
                            msg.error("Incorrect JSON syntax detected."
                                      "Allowed keys: 'github', 'local', 'other'.")
                        # append extra asset data
                        for k in rootkeys:
                            if data[k]:
                                if k == "github":
                                    for e in data[k]:
                                        assets.append(_api_github(e))
                                else:
                                    for e in data[k]:
                                        assets.append(fo.download(e))
                    msg.done("Extra assets added!")
                    print("\n", end="")
            # collect all the specified assets into single directory
            nhpatch = "nhpatch.sh"
            fo.ucopy(os.path.join(self._workdir, "modifications", nhpatch),
                     os.path.join(self._assetdir, nhpatch))
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
        if not os.path.isdir(self._assetdir):
            os.mkdir(self._assetdir)
        else:
            if len(os.listdir(self._assetdir)) != 0:
                msg.note(f"Found an existing \"{self._assetdir.split(os.sep)[-1]}\" folder, clean it?")
                ans = input("[Y/n]: ").lower() if not self._clean else "y"
                if ans == "y":
                    msg.note("Cleaning 'assets' directory..")
                    cm.remove(self._assetdir)
                    os.mkdir(self._assetdir)
                    msg.done("Done!")
                elif ans == "n":
                    msg.cancel("Cancelling asset download.")
                else:
                    msg.error("Invalid option selected.")
        print("\n", end="")

    def _api_rom(self) -> str:
        """Get the latest version of LineageOS ROM.

        :return: URL to the latest ROM .zip archive.
        :rtype: str
        """
        device = self._codename
        romtype = "nightly"
        incr = "ro.build.version.incremental"
        url = f"https://download.lineageos.org/api/v1/{device}/{romtype}/{incr}"
        data = requests.get(url)
        try:
            data = data.json()["response"][0]["url"]
        except Exception:
            exit_flag = False if self._rom_only else True
            msg.error(f"Could not connect to LOS API, HTTP status code: {data.status_code}",
                      dont_exit=exit_flag)
        return data

    def _api_github(self, project: str) -> str:
        """Get the latest version of an artifact from GitHub project.

        :param str project: A name of the project in <owner>/<repo> form.
        :return: URL to the latest artifact from specified GitHub project.
        :rtype: str
        """
        url = f"https://github.com/{project}"
        api_url = f"https://api.github.com/repos/{project}/releases/latest"
        response = requests.get(api_url).json()
        # this will check whether the GitHub API usage is exceeded
        try:
            data = response["message"]
            if "API rate limit" in data:
                msg.error("GitHub API call rate was exceeded, try a bit later.",
                          dont_exit=True)
        except Exception:
            pass
        # get the latest version of GitHub project via API
        try:
            data = response["assets"][0]["browser_download_url"]
        except Exception:
            # if not available via API -- use "git clone"
            rdir = os.path.join(self._assetdir, url.rsplit("/", 1)[1])
            msg.note(f"Non-API GitHub resolution for {project}")
            ccmd.launch(f"rm -rf {rdir}")
            ccmd.launch(f"git clone --depth 1 {url} {rdir}")
            os.chdir(rdir)
            ccmd.launch("rm -rf .git*")
            os.chdir(self._assetdir)
            shutil.make_archive(f"{rdir}", "zip", rdir)
            ccmd.launch(f"rm -rf {rdir}")
            return
        return data
