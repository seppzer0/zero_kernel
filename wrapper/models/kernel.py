import os
import sys
import time
from pathlib import Path

import tools.cleaning as cm
import tools.messages as msg
import tools.commands as ccmd
import tools.fileoperations as fo

from configs import Config as cfg

from utils import Resources as rcs


class KernelBuilder:
    """Kernel builder."""

    _root: Path = cfg.DIR_ROOT

    def __init__(self, codename: str, rom: str, clean: bool, ksu: bool) -> None:
        self._codename = codename
        self._rom = rom
        self._clean = clean
        self._ksu = ksu
        self._rcs = rcs(codename=codename, rom=rom)

    def run(self) -> None:
        msg.banner("s0nh Kernel Builder")
        os.chdir(self._root)
        msg.note("Setting up tools and links..")
        # manage build resources
        self._rcs.path_gen()
        self._rcs.download()
        self._rcs.export_path()
        # clean directories
        self._clean_build()
        if self._clean:
            sys.exit(0)
        # specify localversion
        with open("localversion", "w") as f:
            f.write("~NetHunter-seppzer0")
        msg.done("Done! Tools are configured!")
        # apply various patches
        self._patch_all()
        # build and package
        self._build()
        self._form_release(f"{os.getenv('KNAME', 's0nh')}-{self._ucodename}")

    @property
    def _ucodename(self) -> str:
        """A unified device codename to apply patches for.
        
        E.g., "dumplinger", combining "dumpling" and "cheeseburger",
        both of which share the same kernel source.
        """
        return "dumplinger" if self._codename in ("dumpling", "cheeseburger") else self._codename

    @property
    def _defconfig(self) -> str:
        """Determine defconfig file name based on ROM."""
        return "lineage_oneplus5_defconfig" if self._rom == "los" else "paranoid_defconfig"

    def _clean_build(self) -> None:
        """Clean environment from potential artifacts."""
        print("\n", end="")
        msg.note("Cleaning the build environment..")
        cm.git(self._rcs.paths[self._codename]["path"])
        cm.git(self._rcs.paths["AnyKernel3"]["path"])
        for fn in os.listdir():
            if fn == "localversion" or fn.endswith(".zip"):
                cm.remove(fn)
        msg.done("Done!")

    def _patch_strict_prototypes(self) -> None:
        """A patcher to add compatibility with Clang 15 '-Wstrict-prototype' mandatory rule."""
        msg.note("Patching sources for Clang 15+ compatibility..")
        data = {
            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagchar_core.c":
            ("void diag_ws_init()", "void diag_ws_on_notify()", "void diag_ws_release()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_mux.c":
            ("int diag_mux_init()", "void diag_mux_exit()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_memorydevice.c":
            ("void diag_md_open_all()", "void diag_md_close_all()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_dci.c":
            ("void diag_dci_wakeup_clients()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_bridge.c":
            ("void diagfwd_bridge_exit()", "uint16_t diag_get_remote_device_mask()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_mhi.c":
            ("int diag_mhi_init()", "void diag_mhi_exit()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "camera_v2" /\
            "common" /\
            "msm_camera_tz_util.c":
            ("struct qseecom_handle *msm_camera_tz_get_ta_handle()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "vidc" /\
            "msm_vidc_common.c":
            ("void msm_comm_handle_thermal_event()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "qdsp6v2" /\
            "voice_svc.c":
            ("void msm_bus_rpm_set_mt_mask()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("static int voice_svc_dummy_reg()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("void msm_bus_rpm_set_mt_mask()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "qdsp6v2" /\
            "voice_svc.c":
            ("static int voice_svc_dummy_reg()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "staging" /\
            "qca-wifi-host-cmn" /\
            "hif" /\
            "src" /\
            "ce" /\
            "ce_service.c":
            ("struct ce_ops *ce_services_legacy()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "staging" /\
            "qcacld-3.0" /\
            "core" /\
            "hdd" /\
            "src" /\
            "wlan_hdd_main.c":
            ("hdd_adapter_t *hdd_get_first_valid_adapter()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "thermal" /\
            "msm_thermal-dev.c":
            ("int msm_thermal_ioctl_init()", "void msm_thermal_ioctl_cleanup()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_mdp.c":
            ("struct irq_info *mdss_intr_line()",),

            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_util.c":
            ("struct mdss_util_intf *mdss_get_util_intf()",)
        }
        # PA needs this, LineageOS does not
        if self._rom == "aospa":
            extra_data = {
                self._rcs.paths[self._codename]["path"] /\
                "drivers" /\
                "staging" /\
                "qca-wifi-host-cmn" /\
                "target_if" /\
                "core" /\
                "src" /\
                "target_if_main.c":
                ("struct target_if_ctx *target_if_get_ctx()",),

                self._rcs.paths[self._codename]["path"] /\
                "drivers" /\
                "staging" /\
                "qca-wifi-host-cmn" /\
                "wlan_cfg" /\
                "wlan_cfg.c":
                ("struct wlan_cfg_dp_soc_ctxt *wlan_cfg_soc_attach()",),
            }
            data.update(extra_data)
        # start the patching process
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
        cm.remove(self._rcs.paths["AnyKernel3"]["path"] / "ramdisk")
        cm.remove(self._rcs.paths["AnyKernel3"]["path"] / "models")
        fo.ucopy(
            self._root / "wrapper" / "modifications" / self._ucodename / "anykernel3" / "ramdisk",
            self._rcs.paths["AnyKernel3"]["path"] / "ramdisk"
        )
        fo.ucopy(
            self._root / "wrapper" / "modifications" / self._ucodename / "anykernel3" / "anykernel.sh",
            self._rcs.paths["AnyKernel3"]["path"] / "anykernel.sh"
        )

    def _patch_rtl8812au_source_mod_v5642(self) -> None:
        """Modifications specific to v5.6.4.2 driver version."""
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
        fo.replace_lines(
            Path("Makefile").absolute(),
            og_lines,
            nw_lines
        )
        # same with ioctl_cfg80211.h
        og_lines = (
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 26)) && (LINUX_VERSION_CODE < KERNEL_VERSION(4, 7, 0))",
        )
        nw_lines = (
            "#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 26)) && (LINUX_VERSION_CODE < KERNEL_VERSION(4, 4, 0))",
        )
        fo.replace_lines(
            Path("os_dep", "linux", "ioctl_cfg80211.h").absolute(),
            og_lines,
            nw_lines
        )
        # ...and same with ioctl_cfg80211.c
        og_lines = (
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_SHORT_PREAMBLE;",
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_SHORT_SLOT_TIME;",
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_CTS_PROT;",
            "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_DTIM_PERIOD;",
        )
        nw_lines = (
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_SHORT_PREAMBLE;",
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_SHORT_SLOT_TIME;",
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_CTS_PROT;",
            "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_DTIM_PERIOD;",
        )
        fo.replace_lines(
            Path("os_dep", "linux", "ioctl_cfg80211.c").absolute(),
            og_lines,
            nw_lines
        )

    def _patch_rtl8812au(self) -> None:
        """Patch RTL8812AU sources.
        
        NOTE: .patch files are unreliable in this case, have to replace lines manually
        """
        # copy RTL8812AU sources into kernel path
        msg.note("Adding RTL8812AU drivers into the kernel..")
        fo.ucopy(
            self._rcs.paths["rtl8812au"]["path"],
            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        # modify sources depending on tested driver versions
        os.chdir(
            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        self._patch_rtl8812au_source_mod_v5642()
        cm.remove(".git*")
        os.chdir(self._root)
        # include the driver into build process
        makefile = self._rcs.paths[self._codename]["path"] /\
                   "drivers" /\
                   "net" /\
                   "wireless" /\
                   "realtek" /\
                   "Makefile"
        kconfig = self._rcs.paths[self._codename]["path"] /\
                  "drivers" /\
                  "net" /\
                  "wireless" /\
                  "Kconfig"
        defconfig = self._rcs.paths[self._codename]["path"] /\
                    "arch" /\
                    "arm64" /\
                    "configs" /\
                    self._defconfig
        with open(makefile, "a") as f:
            f.write("obj-$(CONFIG_88XXAU)		+= rtl8812au/")
        fo.insert_before_line(
            kconfig,
            "endif",
            "source \"drivers/net/wireless/realtek/rtl8812au/Kconfig\""
        )
        with open(defconfig, "a") as f:
            extra_configs = (
                "CONFIG_88XXAU=y",
                "CONFIG_MODULE_FORCE_LOAD=y",
                "CONFIG_MODULE_FORCE_UNLOAD=y",
                "CONFIG_CFG80211_WEXT=y",
                "CONFIG_CFG80211_WEXT_EXPORT=y",
                "CONFIG_CONCURRENT_MODE=n",
                "CONFIG_MAC80211=y",
                "CONFIG_RTL8187=y",
                "CONFIG_RTLWIFI=y",
            )
            f.write("\n".join(extra_configs))
            f.write("\n")

    def _patch_ksu(self) -> None:
        """Patch KernelSU into the kernel.

        During this process, a symlink is used to "place" KernelSU
        source into the kernel sources. This is due to the fact that KernelSU
        has an internal mechanism of getting it's version via accessing
        .git data. And having .git data in kernel sources is not ideal.
        """
        msg.note("Adding KernelSU into the kernel..")
        # extract KSU_GIT_VERSION env var manually
        goback = Path.cwd()
        os.chdir(self._rcs.paths["KernelSU"]["path"])
        os.environ["KSU_GIT_VERSION"] = str(
            # formula is retrieved from KernelSU's Makefile itself
            10000 + int(ccmd.launch("git rev-list --count HEAD", get_output=True)) + 200
        )
        os.chdir(goback)
        makefile = self._rcs.paths[self._codename]["path"] /\
                   "drivers" /\
                   "Makefile"
        kconfig = self._rcs.paths[self._codename]["path"] /\
                  "drivers" /\
                  "Kconfig"
        # include into the build process via symlink
        os.symlink(
            self._rcs.paths["KernelSU"]["path"] / cfg.DIR_KERNEL,
            self._rcs.paths[self._codename]["path"] /\
            "drivers" /\
            "kernelsu"
        )
        with open(makefile, "a") as f:
            # TODO: maybe parametrize the "obj-y" with "obj-$(CONFIG_KSU)"
            f.write("obj-y		+= kernelsu/\n")
        fo.insert_before_line(
            kconfig,
            "endmenu",
            "source \"drivers/kernelsu/Kconfig\""
        )
        # update KernelSU source via .patch file
        fo.ucopy(
            self._root / "wrapper" / "modifications" / self._ucodename / cfg.DIR_KERNEL / "kernelsu-compat.patch",
            self._rcs.paths[self._codename]["path"]
        )
        os.chdir(self._rcs.paths[self._codename]["path"])
        for pf in Path.cwd().glob("*.patch"):
            msg.note(f"Applying patch: {pf}")
            ccmd.launch(f"patch -p1 -s --no-backup-if-mismatch -i {pf}")
            os.remove(pf)
        os.chdir(goback)
        # add configs into defconfig
        defconfig = self._rcs.paths[self._codename]["path"] /\
                    "arch" /\
                    "arm64" /\
                    "configs" /\
                    self._defconfig
        with open(defconfig, "a") as f:
            extra_configs = (
                "CONFIG_KSU=y",
                "CONFIG_KSU_DEBUG=y",
                "CONFIG_OVERLAY_FS=y",
                "CONFIG_MODULES=y",
                "CONFIG_MODULE_UNLOAD=y",
                "CONFIG_MODVERSIONS=y",
                "CONFIG_DIAG_CHAR=y",
                "CONFIG_KPROBES=y",
                "CONFIG_HAVE_KPROBES=y",
                "CONFIG_KPROBE_EVENTS=y",
            )
            f.write("\n".join(extra_configs))
            f.write("\n")

    def _patch_kernel(self) -> None:
        """Patch kernel sources."""
        # -Wstrict-prototypes patch to build with Clang 15+
        clang_cmd = f'{self._rcs.paths["clang"]["path"] / "bin" / "clang"} --version'
        clang_ver = ccmd.launch(clang_cmd, get_output=True).split("clang version ")[1].split(".")[0]
        if int(clang_ver) >= 15:
            self._patch_strict_prototypes()
        # apply .patch files;
        # here, patch for KernelSU is ignored;
        #
        # technically it *is* a patch for a *kernel*, but is also applied
        # optionally elsewhere.
        fo.ucopy(
            self._root / "wrapper" / "modifications" / self._ucodename / cfg.DIR_KERNEL,
            self._rcs.paths[self._codename]["path"],
            ("kernelsu-compat.patch",)
        )
        os.chdir(self._rcs.paths[self._codename]["path"])
        for pf in Path.cwd().glob("*.patch"):
            if "kernelsu" not in str(pf):
                msg.note(f"Applying patch: {pf}")
                ccmd.launch(f"patch -p1 -s --no-backup-if-mismatch -i {pf}")
                os.remove(pf)
        # additionally, add support for CONFIG_MAC80211 kernel option
        data = ""
        files = ("tx.c", "mlme.c")
        for fn in files:
            with open(Path("net", "mac80211", fn), "r") as f:
                data = f.read().replace("case IEEE80211_BAND_60GHZ:", "case NL80211_BAND_60GHZ:")
            with open(Path("net", "mac80211", fn), "w") as f:
                f.write(data)
        os.chdir(self._root)

    def _patch_all(self) -> None:
        """Apply various patches."""
        self._patch_anykernel3()
        self._patch_kernel()
        # optionally include KernelSU support
        if self._ksu:
            self._patch_ksu()
        self._patch_rtl8812au()
        msg.done("Patches added!")

    def _build(self) -> None:
        """Build the kernel."""
        print("\n", end="")
        msg.note("Launching the build..")
        os.chdir(self._rcs.paths[self._codename]["path"])
        # launch "make" with the number of all available processing units
        punits = ccmd.launch("nproc --all", get_output=True)
        cmd1 = "make -j{} O=out {} "\
               "ARCH=arm64 "\
               "SUBARCH=arm64 "\
               "HOSTCC=clang "\
               "HOSTCXX=clang+"\
                .format(punits, self._defconfig)
        cmd2 = "make -j{} O=out "\
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
               "STRIP=llvm-strip"\
                .format(punits)
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

        :param name: The name of the archive.
        """
        print("\n", end="")
        msg.note("Forming final ZIP file..")
        fo.ucopy(
            self._rcs.paths[self._codename]["path"] /\
            "out" /\
            "arch" /\
            "arm64" /\
            "boot" /\
            "Image.gz-dtb",
            self._rcs.paths["AnyKernel3"]["path"] / "Image.gz-dtb"
        )
        # define kernel versions: Linux and internal
        with open(self._rcs.paths[self._codename]["path"] / "Makefile") as f:
            head = [next(f) for x in range(3)]
        ver_base = ".".join([i.split("= ")[1].splitlines()[0] for i in head])
        ver_int = os.getenv("KVERSION")
        # form the final ZIP file
        pretag = f"{name}-{self._rom}-ksu" if self._ksu else f"{name}-{self._rom}"
        full_name = f"{pretag}-{ver_base}-{ver_int}"
        kdir = self._root / cfg.DIR_KERNEL
        if not kdir.is_dir():
            os.mkdir(kdir)
        os.chdir(self._rcs.paths["AnyKernel3"]["path"])
        # this is not the best solution, but is the easiest
        cmd = f"zip -r9 {kdir / full_name}.zip . -x *.git* *README* *LICENSE* *placeholder"
        ccmd.launch(cmd)
        os.chdir(self._root)
        msg.done("Done!")
