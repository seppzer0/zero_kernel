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


def validate_settings():
    """Run checks on the build environment."""
    # type of OS that is being used
    if platform.system() == "Windows":
        msg.error("Can't build Linux kernel on a non-Unix machine.")


def export_path(path):
    """Add to PATH."""
    pathenv = f"{path}/bin/"
    # special rules for "android_prebuilts_build-tools"
    if path.split("/")[-1] == "android_prebuilts_build-tools":
        os.environ["PATH"] += os.pathsep + pathenv.replace("/bin/:", "/linux-86/bin/:")
        os.environ["PATH"] += os.pathsep + pathenv.replace("/bin/:", "/path/linux-86/:")
    else:
        os.environ["PATH"] += os.pathsep + pathenv


def clean_dir(directory):
    """Clean up submodule directories."""
    # form the command
    cmd = "git clean -fdx && git reset --hard HEAD"
    if directory == "kernel":
        cmd = f"make clean && {cmd}"
    # launch the cleaning process
    os.chdir(directory)
    ccmd.launch(cmd)
    os.chdir(workdir)


def clean_full():
    """Clean environment from potential artifacts."""
    print("\n", end="")
    msg.note("Cleaning the build environment..")
    clean_dir(paths["android_kernel_oneplus_msm8998"]["path"])
    clean_dir(paths["AnyKernel3"]["path"])
    for file in os.listdir():
        if file == "localversion" or file.endswith(".zip"):
            os.remove(file)
    msg.done("Done!")


def create_vars():
    """Create links to local file paths."""
    global workdir, paths, clang_url
    clang_url = "https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+archive/529a8adc22e54aecc2278960d1a6d84967fb7318/clang-r433403b.tar.gz"
    workdir = os.getenv("ROOTPATH")
    os.chdir(workdir)
    # define paths to git directories ("submodules")
    paths = ""
    with open(os.path.join(workdir, "gitmodules.json")) as f:
        paths = json.load(f)
    for e in paths:
        # convert path into the full form to use later
        paths[e]["path"] = os.path.join(workdir, paths[e]["path"])
        # break data into individual vars
        path = paths[e]["path"]
        url = paths[e]["url"]
        branch = paths[e]["branch"]
        commit = paths[e]["commit"]
        cmd = f"git clone -b {branch} --depth 1 {url} {path}"
        if not os.path.isdir(paths[e]["path"]):
            # it is best to always show the "git clone" command
            ccmd.launch(cmd, "verbose")
        else:
            msg.note(f"Found an existing path: {paths[e]['path']}")
        # checkout a specific commit if it is specified
        if commit:
            cmd = f"git checkout {commit}"
            os.chdir(paths[e])
            ccmd.launch(cmd)
            os.chdir(workdir)


def init(clang_link):
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
    # download and unpack clang
    if clang_link.split("/")[-1] not in os.listdir():
        if clang_link.split("/")[-1].split(".")[0] not in os.listdir():
            msg.note("Downloading Clang..")
            fo.download(clang_link)
            msg.note("Unpacking Clang..")
            with tarfile.open(clang_link.split("/")[-1]) as f:
                f.extractall(clang_link.split("/")[-1].split(".")[0])
    # include Clang into PATH
    paths["clang"] = {
        "path": os.path.join(workdir, clang_link.split("/")[-1].split(".")[0])
    }
    for e in paths:
        export_path(paths[e]["path"])
    msg.done("Done!")


def apply_mods():
    """Apply modifications to the source code."""
    # two devices can have same kernel source
    codename = "dumplinger" if args.codename in ["dumpling", "cheeseburger"] else args.codename
    print("\n", end="")
    msg.note("Applying modifications to the source code..")
    # mac80211
    #fo.ucopy(os.path.join("mods", "kernel", "mac80211"),
    #         os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
    #                      "net",
    #                      "mac80211"))
    # ath9k
    #fo.ucopy(os.path.join("mods", "kernel", "ath9k"),
    #         os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
    #                      "drivers",
    #                      "net",
    #                      "wireless",
    #                      "ath",
    #                      "ath9k"))
    # AnyKernel3 (remove placeholders and inject modified files)
    shutil.rmtree(os.path.join(paths["AnyKernel3"]["path"], "ramdisk"))
    shutil.rmtree(os.path.join(paths["AnyKernel3"]["path"], "modules"))
    fo.ucopy(os.path.join(workdir, "modifications", codename, "anykernel3", "ramdisk"),
             os.path.join(paths["AnyKernel3"]["path"], "ramdisk"))
    fo.ucopy(os.path.join(workdir, "modifications", codename, "anykernel3", "anykernel.sh"),
             os.path.join(paths["AnyKernel3"]["path"], "anykernel.sh"))
    # rtl8812au (apply code patches and remove .git* files)
    msg.note("Adding RTL8812AU drivers into the kernel..")
    fo.ucopy(os.path.join(paths["rtl8812au"]["path"]),
             os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
                          "drivers",
                          "net",
                          "wireless",
                          "realtek",
                          "rtl8812au"))
    os.chdir(os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
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
            shutil.rmtree(elem) if os.path.isdir(elem) else os.remove(elem)
    os.chdir(workdir)
    # include the rtl8812au into build process
    makefile = os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
                            "drivers",
                            "net",
                            "wireless",
                            "realtek",
                            "Makefile")
    kconfig = os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
                           "drivers",
                           "net",
                           "wireless",
                           "Kconfig")
    defconfig = os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
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
    os.chdir(paths["android_kernel_oneplus_msm8998"]["path"])
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
    fo.ucopy(os.path.join(paths["android_kernel_oneplus_msm8998"]["path"],
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
    m5tab = md5sum[0:5]
    with open(os.path.join(paths["android_kernel_oneplus_msm8998"]["path"], "Makefile")) as f:
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
msg.banner("OP5/T LineageOS Kernel builder w/ Kali NetHunter")
validate_settings()
create_vars()
# prepare build
clean_full()
if args.clean:
    sys.exit(0)
init(clang_url)
with open("localversion", "w") as f:
    f.write("~NetHunter-seppzer0")
apply_mods()
# build and pack
build()
form_release("s0nh")
os.chdir(workdir)
