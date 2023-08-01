import os
import sys
import json
import time
import tarfile
from pathlib import Path

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg
import wrapper.tools.commands as ccmd
import wrapper.tools.fileoperations as fo


class KernelBuilder:
    """Kernel builder."""

    def __init__(self, codename: str, losversion: str, clean: bool) -> None:
        self._codename = codename
        self._losversion = losversion
        self._clean = clean
        self._paths = []

    @property
    def _workdir(self) -> os.PathLike:
        return Path(os.getenv("ROOTPATH"))

    def run(self) -> None:
        msg.banner("s0nh Kernel Builder w/ Kali NetHunter")
        os.chdir(self._workdir)
        self._create_vars()
        # clean directories
        self._clean_build()
        if self._clean:
            sys.exit(0)
        # initial setup
        print("\n", end="")
        msg.note("Setting up tools and links..")
        for e in self._paths:
            self._export_path(self._paths[e]["path"])
        msg.done("Done!")
        # specify localversion
        with open("localversion", "w") as f:
            f.write("~NetHunter-seppzer0")
        # apply various patches
        self._patch_all()
        # build and package
        self._build()
        self._form_release(f"{os.getenv('KNAME', 's0nh')}-{self._codename}")

    @property
    def _ucodename(self) -> str:
        """A unified device codename to apply patches for.
        
        E.g, "dumplinger", combining "dumpling" and "cheeseburger",
        both of which share the same kernel source.
        """
        return "dumplinger" if self._codename in ("dumpling", "cheeseburger") else self._codename

    @staticmethod
    def _export_path(path: os.PathLike) -> None:
        """Add path to PATH.

        :param str path: A path that is being added to PATH.
        """
        pathenv = str(f"{path}/bin/")
        # special rules for "android_prebuilts_build-tools"
        if path.name == "android_prebuilts_build-tools":
            os.environ["PATH"] += os.pathsep + pathenv.replace("/bin/:", "/linux-86/bin/:")
            os.environ["PATH"] += os.pathsep + pathenv.replace("/bin/:", "/path/linux-86/:")
        else:
            os.environ["PATH"] += os.pathsep + pathenv

    def _clean_build(self) -> None:
        """Clean environment from potential artifacts."""
        print("\n", end="")
        msg.note("Cleaning the build environment..")
        cm.git(self._paths[self._codename]["path"])
        cm.git(self._paths["AnyKernel3"]["path"])
        for fn in os.listdir():
            if fn == "localversion" or fn.endswith(".zip"):
                cm.remove(fn)
        msg.done("Done!")

    def _create_vars(self) -> None:
        """Create links to local file paths."""
        os.chdir(self._workdir)
        # define paths
        tools = ""
        device = ""
        with open(self._workdir / "wrapper" / "manifests" / "tools.json") as f:
            tools = json.load(f)
        with open(self._workdir / "wrapper" / "manifests" / "devices.json") as f:
            data = json.load(f)
            device = {self._codename: data[self._codename]}
        # join tools and devices manifests
        self._paths = {**tools, **device}
        for e in self._paths:
            # convert path into the full form to use later as a Path() object
            self._paths[e]["path"] = self._workdir / self._paths[e]["path"]
            # break data into individual required vars
            path = self._paths[e]["path"]
            url = self._paths[e]["url"]
            # break further processing into "generic" and "git" groups
            ftype = self._paths[e]["type"]
            if ftype == "generic":
                # download and unpack
                # NOTE: this is specific, for .tar.gz files
                if path.name not in os.listdir():
                    fn = url.split("/")[-1]
                    dn = fn.split(".")[0]
                    if fn not in os.listdir() and dn not in os.listdir():
                        fo.download(url)
                    msg.note(f"Unpacking {fn}..")
                    with tarfile.open(fn) as f:
                        f.extractall(path)
                    cm.remove(fn)
                    msg.done("Done!")
                else:
                    msg.note(f"Found an existing path: {path}")
            elif ftype == "git":
                # break data into individual vars
                branch = self._paths[e]["branch"]
                commit = self._paths[e]["commit"]
                cmd = f"git clone -b {branch} --depth 1 {url} {path}"
                if not path.is_dir():
                    ccmd.launch(cmd)
                    # checkout a specific commit if it is specified
                    if commit:
                        cmd = f"git checkout {commit}"
                        os.chdir(path)
                        ccmd.launch(cmd)
                        os.chdir(self._workdir)
                else:
                    msg.note(f"Found an existing path: {path}")
            else:
                msg.error("Invalid resource type detected. Use only: generic, git.")


    def _patch_strict_prototypes(self) -> None:
        """A patcher to add compatibility with Clang 15 '-Wstrict-prototype' mandatory rule."""
        msg.note("Patching sources for Clang 15+ compatibility..")
        data = {
            self._paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagchar_core.c":
            ("void diag_ws_init()", "void diag_ws_on_notify()", "void diag_ws_release()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_mux.c":
            ("int diag_mux_init()", "void diag_mux_exit()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_memorydevice.c":
            ("void diag_md_open_all()", "void diag_md_close_all()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_dci.c":
            ("void diag_dci_wakeup_clients()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_bridge.c":
            ("void diagfwd_bridge_exit()", "uint16_t diag_get_remote_device_mask()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_mhi.c":
            ("int diag_mhi_init()", "void diag_mhi_exit()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "camera_v2" /\
            "common" /\
            "msm_camera_tz_util.c":
            ("struct qseecom_handle *msm_camera_tz_get_ta_handle()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "vidc" /\
            "msm_vidc_common.c":
            ("void msm_comm_handle_thermal_event()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "qdsp6v2" /\
            "voice_svc.c":
            ("void msm_bus_rpm_set_mt_mask()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("static int voice_svc_dummy_reg()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("void msm_bus_rpm_set_mt_mask()",),

            self._paths[self._codename]["path"]/\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "qdsp6v2" /\
            "voice_svc.c":
            ("static int voice_svc_dummy_reg()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "staging" /\
            "qca-wifi-host-cmn" /\
            "hif" /\
            "src" /\
            "ce" /\
            "ce_service.c":
            ("struct ce_ops *ce_services_legacy()",),

            #self._paths[self._codename]["path"] /\
            #"drivers" /\
            #"staging" /\
            #"qca-wifi-host-cmn" /\
            #"target_if" /\
            #"core" /\
            #"src" /\
            #"target_if_main.c":
            #("struct target_if_ctx *target_if_get_ctx()",),

            #self._paths[self._codename]["path"] /\
            #"drivers" /\
            #"staging" /\
            #"qca-wifi-host-cmn" /\
            #"wlan_cfg" /\
            #"wlan_cfg.c":
            #("struct wlan_cfg_dp_soc_ctxt *wlan_cfg_soc_attach()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "staging" /\
            "qcacld-3.0" /\
            "core" /\
            "hdd" /\
            "src" /\
            "wlan_hdd_main.c":
            ("hdd_adapter_t *hdd_get_first_valid_adapter()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "thermal" /\
            "msm_thermal-dev.c":
            ("int msm_thermal_ioctl_init()", "void msm_thermal_ioctl_cleanup()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_mdp.c":
            ("struct irq_info *mdss_intr_line()",),

            self._paths[self._codename]["path"] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_util.c":
            ("struct mdss_util_intf *mdss_get_util_intf()",)
        }
        contents = ""
        for fname, funcnames in data.items():
            with open(fname, "r") as f:
                contents = f.read()
            # replace: "()" -> "(void)"
            for func in funcnames:
                contents = contents.replace(func, func.replace("()", "(void)"))
            with open(fname, "w") as f:
                f.write(contents)
        msg.done("Done!")

    def _patch_anykernel3(self) -> None:
        """Patch AnyKernel3 sources."""
        cm.remove(self._paths["AnyKernel3"]["path"] / "ramdisk")
        cm.remove(self._paths["AnyKernel3"]["path"] / "models")
        fo.ucopy(
            self._workdir / "wrapper" / "modifications" / self._ucodename / "anykernel3" / "ramdisk",
            self._paths["AnyKernel3"]["path"] / "ramdisk"
        )
        fo.ucopy(
            self._workdir / "wrapper" / "modifications" / self._ucodename / "anykernel3" / "anykernel.sh",
            self._paths["AnyKernel3"]["path"] / "anykernel.sh"
        )

    def _patch_rtl8812au_source_mod_v5642(self) -> None:
        # modifying Makefile
        og_lines = (
            "#EXTRA_CFLAGS += -Wno-parentheses-equality",
            "#EXTRA_CFLAGS += -Wno-pointer-bool-conversion",
            "$(MAKE) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) -C $(KSRC) M=$(shell pwd)  modules",
            "CONFIG_PLATFORM_I386_PC = y",
            "CONFIG_PLATFORM_ANDROID_ARM64 = n"
        )
        nw_lines = (
            "EXTRA_CFLAGS += -Wno-parentheses-equality",
            "EXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-parentheses-equality\nEXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-pragma-pack",
            '$(MAKE) ARCH=$(ARCH) SUBARCH=$(ARCH) REAL_CC=${CC_DIR}/clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=$(CROSS_COMPILE) -C $(KSRC) M=$(shell pwd) O="$(KBUILD_OUTPUT)" modules',
            "CONFIG_PLATFORM_I386_PC = n",
            "CONFIG_PLATFORM_ANDROID_ARM64 = y\nCONFIG_CONCURRENT_MODE = n",
        )
        with open("Makefile") as data:
            with open("Makefile_new", 'w') as new_data:
                for line in data:
                    for indx, key in enumerate(og_lines):
                        if key in line:
                            msg.note(f"Replacing {key} with {nw_lines[indx]}")
                            line = line.replace(key, nw_lines[indx])
                    new_data.write(line)
        os.replace("Makefile_new", "Makefile")
        # same with ioctl_cfg80211.h
        og_lines = (
            #"#define NL80211_BAND_5GHZ IEEE80211_BAND_5GHZ",
            #"#define NUM_NL80211_BANDS IEEE80211_NUM_BANDS",
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 26)) && (LINUX_VERSION_CODE < KERNEL_VERSION(4, 7, 0))",
        )
        nw_lines = (
            #"#define NL80211_BAND_5GHZ IEEE80211_BAND_5GHZ\n#define IEEE80211_BAND_2GHZ 0\n#define IEEE80211_BAND_5GHZ 0",
            #"#define NUM_NL80211_BANDS IEEE80211_NUM_BANDS\n#define IEEE80211_NUM_BANDS 0",
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 26)) && (LINUX_VERSION_CODE < KERNEL_VERSION(4, 4, 0))",
        )
        with open(Path("os_dep", "linux", "ioctl_cfg80211.h")) as data:
            with open(Path("os_dep", "linux", "ioctl_cfg80211_new.h"), 'w') as new_data:
                for line in data:
                    for indx, key in enumerate(og_lines):
                        if key in line:
                            msg.note(f"Replacing {key} with {nw_lines[indx]}")
                            line = line.replace(key, nw_lines[indx])
                    new_data.write(line)
        os.replace(
            Path("os_dep", "linux", "ioctl_cfg80211_new.h"),
            Path("os_dep", "linux", "ioctl_cfg80211.h")
        )
        # ...and same with ioctl_cfg80211.c
        og_lines = (
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_SHORT_PREAMBLE;",
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_SHORT_SLOT_TIME;",
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_CTS_PROT;",
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_DTIM_PERIOD;",
            #", WLAN_STATUS_SUCCESS, GFP_ATOMIC);",
        )
        nw_lines = (
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_SHORT_PREAMBLE;",
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_SHORT_SLOT_TIME;",
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_CTS_PROT;",
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_DTIM_PERIOD;",
            #", WLAN_STATUS_SUCCESS, GFP_ATOMIC, NL80211_TIMEOUT_UNSPECIFIED);",
        )
        with open(Path("os_dep", "linux", "ioctl_cfg80211.c")) as data:
            with open(Path("os_dep", "linux", "ioctl_cfg80211_new.c"), 'w') as new_data:
                for line in data:
                    for indx, key in enumerate(og_lines):
                        if key in line:
                            msg.note(f"Replacing {key} with {nw_lines[indx]}")
                            line = line.replace(key, nw_lines[indx])
                    new_data.write(line)
        os.replace(
            Path("os_dep", "linux", "ioctl_cfg80211_new.c"),
            Path("os_dep", "linux", "ioctl_cfg80211.c")
        )

    def _patch_rtl8812au_source_mod_v534(self) -> None:
        # modifying Makefile
        path_for_topdir = self._paths[self._codename]["path"] /\
                          "out" /\
                          "drivers" /\
                          "net" /\
                          "wireless" /\
                          "realtek" /\
                          "rtl8812au"
        og_lines = (
            "EXTRA_CFLAGS += -Wno-unused-function",
            "CONFIG_PLATFORM_I386_PC = n",
            "########### COMMON  #################################",
        )
        nw_lines = (
            "EXTRA_CFLAGS += -Wno-unused-function\nEXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-parentheses-equality\nEXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-pragma-pack",
            "CONFIG_PLATFORM_I386_PC = n\nCONFIG_PLATFORM_ANDROID_ARM64 = y\nCONFIG_CONCURRENT_MODE = n",
            f"export TopDIR ?= {str(path_for_topdir)}\n########### COMMON  #################################",
        )
        with open("Makefile") as data:
            with open("Makefile_new", 'w') as new_data:
                for line in data:
                    for indx, key in enumerate(og_lines):
                        if key in line:
                            msg.note(f"Replacing {key} with {nw_lines[indx]}")
                            line = line.replace(key, nw_lines[indx])
                    new_data.write(line)
        os.replace("Makefile_new", "Makefile")
        # fixing Kconfig
        kconfig_data = ""
        with open("Kconfig", "r") as f:
            kconfig_data = f.read().replace("RTL88XXAU", "88XXAU")
        with open("Kconfig", "w") as f:
            f.write(kconfig_data)


    def _patch_rtl8812au(self) -> None:
        """Patch RTL8812AU sources.
        
        NOTE: .patch files are unreliable in this case, have to replace lines manually
        """
        # copy RTL8812AU sources into kernel path
        msg.note("Adding RTL8812AU drivers into the kernel..")
        fo.ucopy(
            self._paths["rtl8812au"]["path"],
            self._paths[self._codename]["path"] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        # modify sources depending on tested driver versions
        os.chdir(
            self._paths[self._codename]["path"] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        self._patch_rtl8812au_source_mod_v5642()
        #self._patch_rtl8812au_source_mod_v534()
        # clean .git* files
        for elem in os.listdir():
            if elem.startswith(".git"):
                cm.remove(elem)
        os.chdir(self._workdir)
        # include the driver into build process
        makefile = self._paths[self._codename]["path"] /\
                   "drivers" /\
                   "net" /\
                   "wireless" /\
                   "realtek" /\
                   "Makefile"
        kconfig = self._paths[self._codename]["path"] /\
                  "drivers" /\
                  "net" /\
                  "wireless" /\
                  "Kconfig"
        defconfig = self._paths[self._codename]["path"] /\
                    "arch" /\
                    "arm64" /\
                    "configs" /\
                    "lineage_oneplus5_defconfig"
        with open(makefile, "a") as f:
            f.write("obj-$(CONFIG_88XXAU)		+= rtl8812au/")
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
        with open(defconfig, "a") as f:
            extra_configs = (
                "CONFIG_88XXAU=y",
                "CONFIG_MODULE_FORCE_LOAD=y",
                "CONFIG_MODULE_FORCE_UNLOAD=y",
                "CONFIG_CFG80211_WEXT=y",
                "CONFIG_CFG80211_WEXT_EXPORT=y",
                "CONFIG_CONCURRENT_MODE=n",
                "CONFIG_MAC80211=y",
            )
            f.write("\n".join(extra_configs))
            f.write("\n")

    def _patch_kernel(self) -> None:
        """Patch kernel sources."""
        # -Wstrict-prototypes patch to build with Clang 15+
        clang_cmd = f'{self._paths["clang"]["path"] / "bin" / "clang"} --version'
        clang_ver = ccmd.launch(clang_cmd, get_output=True).split("clang version ")[1].split(".")[0]
        if int(clang_ver) >= 15:
            self._patch_strict_prototypes()
        # apply .patch files
        fo.ucopy(
            self._workdir / "wrapper" / "modifications" / self._ucodename / "kernel",
            self._paths[self._codename]["path"]
        )
        os.chdir(self._paths[self._codename]["path"])
        for pf in Path.cwd().glob("*.patch"):
            msg.note(f"Applying patch: {pf}")
            ccmd.launch(f"patch -p1 -s --no-backup-if-mismatch -i {pf}")
            os.remove(pf)
        # additionally add support for CONFIG_MAC80211 kernel option
        data = ""
        files = ("tx.c", "mlme.c")
        for fn in files:
            with open(Path("net", "mac80211", fn), "r") as f:
                data = f.read().replace("case IEEE80211_BAND_60GHZ:", "case NL80211_BAND_60GHZ:")
            with open(Path("net", "mac80211", fn), "w") as f:
                f.write(data)
        os.chdir(self._workdir)

    def _patch_all(self) -> None:
        """Apply various patches."""
        self._patch_anykernel3()
        self._patch_kernel()
        self._patch_rtl8812au()
        msg.done("Patches added!")

    def _build(self) -> None:
        """Build the kernel."""
        print("\n", end="")
        msg.note("Launching the build..")
        os.chdir(self._paths[self._codename]["path"])
        # launch "make" with the number of all available processing units
        punits = ccmd.launch("nproc --all", get_output=True)
        cmd1 = f"make -j{punits} O=out lineage_oneplus5_defconfig "\
               "ARCH=arm64 "\
               "SUBARCH=arm64 "\
               "HOSTCC=clang "\
               "HOSTCXX=clang+"
        cmd2 = f"make -j{punits} O=out "\
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
               "LLVM=1 "\
               "LLVM_IAS=1 "\
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

    def _form_release(self, name: str) -> None:
        """Pack build artifacts into a .zip archive.

        :param str name: The name of the archive.
        """
        print("\n", end="")
        msg.note("Forming final ZIP file..")
        fo.ucopy(
            self._paths[self._codename]["path"] /\
            "out" /\
            "arch" /\
            "arm64" /\
            "boot" /\
            "Image.gz-dtb",
            self._paths["AnyKernel3"]["path"] / "Image.gz-dtb"
        )
        # kernel version and timestamp
        with open(self._paths[self._codename]["path"] / "Makefile") as f:
            head = [next(f) for x in range(3)]
        kernelversion = ".".join([i.split("= ")[1].split("\n")[0] for i in head])
        buildtime = time.strftime("%Y%m%d")
        # form the final ZIP file
        name = f"{name}-{kernelversion}-{buildtime}"
        kdir = self._workdir / "kernel"
        if not kdir.is_dir():
            os.mkdir(kdir)
        os.chdir(self._paths["AnyKernel3"]["path"])
        # this is not the best solution, but is the easiest
        cmd = f"zip -r9 {kdir / name}.zip . -x *.git* *README* *LICENSE* *placeholder"
        ccmd.launch(cmd)
        os.chdir(self._workdir)
        msg.done("Done!")
