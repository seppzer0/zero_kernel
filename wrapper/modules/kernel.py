import os
import sys
import json
import time
import shutil
import hashlib
import tarfile
import zipfile
import argparse
import requests
import platform
import fileinput
import subprocess
# append to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import cleanmaster as cm
import customcmd as ccmd
import fileoperations as fo
import messagedecorator as msg


def parse_args():
    """Parse the script arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("codename",
                        help="select device codename")
    parser.add_argument("losversion",
                        help="select LineageOS version to build the kernel for")
    parser.add_argument("-c", "--clean",
                        dest="clean",
                        action="store_true",
                        help="don't build anything, just clean the environment")
    global args
    args = parser.parse_args()


def export_path(path):
    """Add to PATH."""
    pathenv = f"{path}/bin/"
    # special rules for "android_prebuilts_build-tools"
    if path.split("/")[-1] == "android_prebuilts_build-tools":
        os.environ["PATH"] += os.pathsep + pathenv.replace("/bin/:", "/linux-86/bin/:")
        os.environ["PATH"] += os.pathsep + pathenv.replace("/bin/:", "/path/linux-86/:")
    else:
        os.environ["PATH"] += os.pathsep + pathenv


def clean_build():
    """Clean environment from potential artifacts."""
    print("\n", end="")
    msg.note("Cleaning the build environment..")
    cm.git(paths[codename]["path"])
    cm.git(paths["AnyKernel3"]["path"])
    for file in os.listdir():
        if file == "localversion" or file.endswith(".zip"):
            cm.remove(file)
    msg.done("Done!")


def create_vars():
    """Create links to local file paths."""
    global workdir, paths, codename
    workdir = os.getenv("ROOTPATH")
    codename = args.codename
    os.chdir(workdir)
    # define paths
    tools = ""
    device = ""
    paths = ""
    with open(os.path.join(workdir, "manifests", "tools.json")) as f:
        tools = json.load(f)
    with open(os.path.join(workdir, "manifests", "devices.json")) as f:
        data = json.load(f)
        device = {codename: data[codename]}
    # join tools and devices manifests
    paths = {**tools, **device}
    for e in paths:
        # convert path into the full form to use later
        paths[e]["path"] = os.path.join(workdir, paths[e]["path"])
        # break data into individual required vars
        path = paths[e]["path"]
        url = paths[e]["url"]
        # break further processing into "generic" and "git" groups
        ftype = paths[e]["type"]
        if ftype == "generic":
            # download and unpack
            # NOTE: this is specific, for .tar.gz files
            if path not in os.listdir():
                fn = url.split("/")[-1]
                dn = fn.split(".")[0]
                if fn not in os.listdir() and dn not in os.listdir():
                    fo.download(url)
                msg.note(f"Unpacking {fn}..")
                with tarfile.open(fn) as f:
                    f.extractall(path)
                cm.remove(fn)
        elif ftype == "git":
            # break data into individual vars
            branch = paths[e]["branch"]
            commit = paths[e]["commit"]
            cmd = f"git clone -b {branch} --depth 1 {url} {path}"
            if not os.path.isdir(path):
                # it is best to always show the "git clone" command
                ccmd.launch(cmd, "verbose")
                # checkout a specific commit if it is specified
                if commit:
                    cmd = f"git checkout {commit}"
                    os.chdir(path)
                    ccmd.launch(cmd)
                    os.chdir(workdir)
            else:
                msg.note(f"Found an existing path: {path}")
        else:
            msg.error("Invalid resource type detected. Use only: custom, git.")


def init():
    """Run initial preparations for the build."""
    # install required packages
    print("\n", end="")
    msg.note("Setting up tools and links..")
    cmd = "sudo apt update && "\
          "sudo apt install -y "\
          "libssl-dev "\
          "wget "\
          "git "\
          "make "\
          "gcc "\
          "zip"
    ccmd.launch(cmd)
    for e in paths:
        export_path(paths[e]["path"])
    msg.done("Done!")


def modify():
    """Apply modifications to the source code."""
    # two devices can have same kernel source
    print("\n", end="")
    msg.note("Applying modifications to the source code..")
    # mac80211
    #fo.ucopy(os.path.join("mods", "kernel", "mac80211"),
    #         os.path.join(paths[codename]["path"],
    #                      "net",
    #                      "mac80211"))
    # ath9k
    #fo.ucopy(os.path.join("mods", "kernel", "ath9k"),
    #         os.path.join(paths[codename]["path"],
    #                      "drivers",
    #                      "net",
    #                      "wireless",
    #                      "ath",
    #                      "ath9k"))
    # AnyKernel3 (remove placeholders and inject modified files)
    cm.remove(os.path.join(paths["AnyKernel3"]["path"], "ramdisk"))
    cm.remove(os.path.join(paths["AnyKernel3"]["path"], "modules"))
    mcodename = "dumplinger" if args.codename in ["dumpling", "cheeseburger"] else args.codename
    fo.ucopy(os.path.join(workdir, "modifications", mcodename, "anykernel3", "ramdisk"),
             os.path.join(paths["AnyKernel3"]["path"], "ramdisk"))
    fo.ucopy(os.path.join(workdir, "modifications", mcodename, "anykernel3", "anykernel.sh"),
             os.path.join(paths["AnyKernel3"]["path"], "anykernel.sh"))
    # rtl8812au (apply code patches and remove .git* files)
    msg.note("Adding RTL8812AU drivers into the kernel..")
    fo.ucopy(os.path.join(paths["rtl8812au"]["path"]),
             os.path.join(paths[codename]["path"],
                          "drivers",
                          "net",
                          "wireless",
                          "realtek",
                          "rtl8812au"))
    os.chdir(os.path.join(paths[codename]["path"],
                          "drivers",
                          "net",
                          "wireless",
                          "realtek",
                          "rtl8812au"))
    # NOTE: PATCHES ARE UNRELIABLE, have to replace strings manually
    # patch the Makefile
    og_lines = [
        "#EXTRA_CFLAGS += -Wno-parentheses-equality",
        "#EXTRA_CFLAGS += -Wno-pointer-bool-conversion",
        "$(MAKE) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) -C $(KSRC) M=$(shell pwd)  modules",
        ]
    nw_lines = [
        "EXTRA_CFLAGS += -Wno-parentheses-equality",
        "EXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-parentheses-equality\nEXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-pragma-pack",
        '$(MAKE) ARCH=$(ARCH) SUBARCH=$(ARCH) REAL_CC=${CC_DIR}/clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=$(CROSS_COMPILE) -C $(KSRC) M=$(shell pwd) O="$(KBUILD_OUTPUT)" modules',
    ]
    with open("Makefile") as data:
        with open("Makefile_new", 'w') as new_data:
            for line in data:
                for indx, key in enumerate(og_lines):
                    if key in line:
                        msg.note(f"Replacing {key} with {nw_lines[indx]}")
                        line = line.replace(key, nw_lines[indx])
                new_data.write(line)
    os.replace("Makefile_new", "Makefile")
    # same with ioctl
    og_lines = [
        "#define NL80211_BAND_5GHZ IEEE80211_BAND_5GHZ",
        "#define NUM_NL80211_BANDS IEEE80211_NUM_BANDS"
        ]
    nw_lines = [
        "#define NL80211_BAND_5GHZ IEEE80211_BAND_5GHZ\n#define IEEE80211_BAND_2GHZ 0\n#define IEEE80211_BAND_5GHZ 0",
        "#define NUM_NL80211_BANDS IEEE80211_NUM_BANDS\n#define IEEE80211_NUM_BANDS 0"
    ]
    with open(os.path.normpath("os_dep/linux/ioctl_cfg80211.h")) as data:
        with open(os.path.normpath("os_dep/linux/ioctl_cfg80211_new.h"), 'w') as new_data:
            for line in data:
                for indx, key in enumerate(og_lines):
                    if key in line:
                        msg.note(f"Replacing {key} with {nw_lines[indx]}")
                        line = line.replace(key, nw_lines[indx])
                new_data.write(line)
    os.replace(os.path.normpath("os_dep/linux/ioctl_cfg80211_new.h"),
               os.path.normpath("os_dep/linux/ioctl_cfg80211.h"))
    # clean .git* files
    for elem in os.listdir():
        if elem.startswith(".git"):
            cm.remove(elem)
    os.chdir(workdir)
    # include the rtl8812au into build process
    makefile = os.path.join(paths[codename]["path"],
                            "drivers",
                            "net",
                            "wireless",
                            "realtek",
                            "Makefile")
    kconfig = os.path.join(paths[codename]["path"],
                           "drivers",
                           "net",
                           "wireless",
                           "Kconfig")
    defconfig = os.path.join(paths[codename]["path"],
                             "arch",
                             "arm64",
                             "configs",
                             "lineage_oneplus5_defconfig")
    # append to Makefile
    with open(makefile, "a") as f:
        f.write("obj-$(CONFIG_88XXAU)		+= rtl8812au/")
    # inject into Kconfig
    with open(kconfig, "r+") as f:
        a = [x.rstrip() for x in f]
        index = 0
        for item in a:
            if item.startswith("endif"):
                a.insert(index, "source \"drivers/net/wireless/realtek/rtl8812au/Kconfig\"")
                break
            index += 1
        f.seek(0)
        f.truncate()
        for line in a:
            f.write(line + "\n")
    # append to defconfig
    with open(defconfig, "a") as f:
        f.write("CONFIG_88XXAU=y")
    msg.done("Patches added!")
    msg.done("Done!")


def build():
    """Build the kernel."""
    print("\n", end="")
    msg.note("Launching the build..")
    os.chdir(paths[codename]["path"])
    cmd1 = "make -j\"$(nproc --all)\" O=out lineage_oneplus5_defconfig "\
           "ARCH=arm64 "\
           "SUBARCH=arm64 "\
           "HOSTCC=clang "\
           "HOSTCXX=clang+"
    cmd2 = "make -j\"$(nproc --all)\" O=out "\
           "ARCH=arm64 "\
           "SUBARCH=arm64 "\
           "CROSS_COMPILE=aarch64-linux-android- "\
           "CROSS_COMPILE_ARM32=arm-linux-androideabi- "\
           "CLANG_TRIPLE=aarch64-linux-gnu- "\
           "HOSTCC=clang "\
           "HOSTCXX=clang++ "\
           "CC=clang "\
           "CXX=clang++ "\
           "AR=llvm-ar "\
           "NM=llvm-nm "\
           "AS=llvm-as "\
           "OBJCOPY=llvm-objcopy "\
           "OBJDUMP=llvm-objdump "\
           "STRIP=llvm-strip"
    # launch and time the build process
    time_start = time.time()
    ccmd.launch(cmd1)
    ccmd.launch(cmd2)
    time_stop = time.time()
    time_elapsed = time_stop - time_start
    # convert elapsed time into human readable format
    secs = time_elapsed % (24 * 3600)
    hours = secs // 3600
    secs %= 3600
    mins = secs // 60
    secs %= 60
    msg.done("Done! Time spent for the build: %02d:%02d:%02d" % (hours, mins, secs))


def form_release(name):
    """Pack build artifacts."""
    print("\n", end="")
    msg.note("Forming final ZIP file..")
    fo.ucopy(os.path.join(paths[codename]["path"],
                          "out",
                          "arch",
                          "arm64",
                          "boot",
                          "Image.gz-dtb"),
             os.path.join(paths["AnyKernel3"]["path"],
                          "Image.gz-dtb"))
    # MD5 hash, kernel version and timestamp
    md5sum = hashlib.md5(os.path.join(paths["AnyKernel3"]["path"],
                                      "Image.gz-dtb")
                         .encode('utf-8')).hexdigest()
    with open(os.path.join(paths[codename]["path"], "Makefile")) as f:
        head = [next(f) for x in range(3)]
    kernelversion = ".".join([i.split("= ")[1].split("\n")[0] for i in head])
    buildtime = time.strftime("%Y%m%d")
    # form the final ZIP file
    name = f"{name}-{kernelversion}-{buildtime}"
    reldir = os.path.join(workdir, "release")
    if not os.path.isdir(reldir):
        os.mkdir(reldir)
    os.chdir(paths["AnyKernel3"]["path"])
    # this is not the best solution, but is the easiest
    cmd = f"zip -r9 {workdir + os.sep}release/{name}.zip * -x .git* README.md *placeholder"
    ccmd.launch(cmd)
    os.chdir(workdir)
    msg.done("Done!")


# launch the script
parse_args()
msg.banner("s0nh Kernel Builder w/ Kali NetHunter")
create_vars()
# prepare build
clean_build()
if args.clean:
    sys.exit(0)
init()
with open("localversion", "w") as f:
    f.write("~NetHunter-seppzer0")
modify()
# build and pack
build()
form_release(f"{os.getenv('KNAME')}-{args.codename}")
os.chdir(workdir)
