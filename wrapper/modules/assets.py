import io
import os
import sys
import json
import shutil
import argparse
import requests
# append to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import customcmd as ccmd
import fileoperations as fo
import messagedecorator as msg


def parse_args(description="An asset downloader for kernel flashing."):
    """Parse the script arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("codename",
                        help="select device codename"),
    parser.add_argument("losversion",
                        help="select LineageOS version"),
    parser.add_argument("chroot",
                        choices=["full", "minimal"],
                        help="select kali chroot type")
    parser.add_argument("--extra-assets",
                        dest="extra_assets",
                        help="select a JSON file in 'scripts' with extra assets")
    parser.add_argument("--clean",
                        dest="clean",
                        action="store_true",
                        help="autoclean 'assets' folder if it exists")
    global args
    args = parser.parse_args()


def init():
    """Initiate some checks before execution."""
    global workdir, assetdir
    workdir = os.getenv("ROOTPATH")
    assetdir = os.path.join(workdir, "assets")
    os.chdir(workdir)
    # directory validation
    if not os.path.isdir(assetdir):
        os.mkdir(assetdir)
    else:
        if len(os.listdir(assetdir)) != 0:
            msg.note(f"Found an existing \"{assetdir.split(os.sep)[-1]}\" folder, clean it?")
            ans = input("[Y/n]: ").lower() if not args.clean else "y"
            if ans == "y":
                msg.note("Cleaning 'assets' directory..")
                shutil.rmtree(assetdir)
                os.mkdir(assetdir)
                msg.done("Done!")
            elif ans == "n":
                msg.cancel("Cancelling asset download.")
            else:
                msg.error("Invalid option selected.")
    print("\n", end="")


def api_los_rom():
    """Get the latest version of LineageOS ROM."""
    device = args.codename
    romtype = "nightly"
    incr = "ro.build.version.incremental"
    url = f"https://download.lineageos.org/api/v1/{device}/{romtype}/{incr}"
    data = requests.get(url)
    try:
        data = data.json()["response"][-1]["url"]
    except Exception:
        msg.error(f"Couldn't connect to LOS API, HTTP status code: {data.status_code}",
                  dont_exit=True)
    return data


def api_github(project):
    """Get the latest version of an artifact from GitHub project."""
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
        rdir = os.path.join(assetdir, url.rsplit("/", 1)[1])
        msg.note(f"Non-API GitHub download for {project}")
        ccmd.launch(f"rm -rf {rdir}")
        ccmd.launch(f"git clone --depth 1 {url} {rdir}")
        os.chdir(rdir)
        ccmd.launch("rm -rf .git*")
        os.chdir(assetdir)
        shutil.make_archive(f"{rdir}", "zip", rdir)
        ccmd.launch(f"rm -rf {rdir}")
        return
    return data


# launch the script
parse_args()
msg.banner("OP5/T NetHunter Kernel Asset Collector")
init()
assets = [
    api_los_rom(),
    api_github("engstk/android_device_oneplus_cheeseburger"),
    api_github("topjohnwu/Magisk"),
    api_github("Magisk-Modules-Repo/wirelessFirmware"),
    "https://store.nethunter.com/repo/com.offsec.nethunter_2022040200.apk",
    "https://store.nethunter.com/repo/com.offsec.nhterm_2020040100.apk",
    "https://store.nethunter.com/repo/org.pocketworkstation.pckeyboard_1041001.apk",
    f"https://kali.download/nethunter-images/current/rootfs/kalifs-arm64-{args.chroot}.tar.xz"
]
# read extra assets from JSON file
if args.extra_assets:
    extra_json = os.path.join(workdir, args.extra_assets)
    if os.path.isfile(extra_json):
        print("\n", end="")
        msg.note("Applying extra assets..")
        with open(extra_json) as f:
            data = json.load(f)
            # validate the input JSON
            rootkeys = ["github", "local", "other"]
            if not all(le in data.keys() for le in rootkeys):
                msg.error("Incorrect JSON syntax detected."
                          "Allowed keys: 'github', 'local', 'other'.")
            # append extra asset data
            for k in rootkeys:
                if data[k]:
                    if k == "github":
                        for e in data[k]:
                            assets.append(api_github(e))
                    else:
                        for e in data[k]:
                            assets.append(fo.download(e))
        msg.done("Extra assets added!")
        print("\n", end="")
# collect all the specified assets into single directory
nhpatch = "nhpatch.sh"
fo.ucopy(os.path.join(workdir, "modifications", nhpatch),
         os.path.join(assetdir, nhpatch))
os.chdir(assetdir)
for e in assets:
    if e:
        fo.download(e)
os.chdir(workdir)
print("\n", end="")
msg.done("Assets collected!")
