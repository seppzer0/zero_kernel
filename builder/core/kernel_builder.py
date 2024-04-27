import os
import sys
import time
from pathlib import Path
from pydantic import BaseModel

from builder.tools import cleaning as cm, commands as ccmd, fileoperations as fo, messages as msg
from builder.configs import DirectoryConfig as dcfg
from builder.managers import ResourceManager
from builder.interfaces import IKernelBuilder


class KernelBuilder(BaseModel, IKernelBuilder):
    """Kernel builder.

    :param str codename: Device codename.
    :param str base: Kernel source base.
    :param str lkv: Linux kernel version.
    :param bool clean_kernel: Flag to clean folder with kernel sources.
    :param bool ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    lkv: str
    clean_kernel: bool
    ksu: bool
    rm: ResourceManager

    @staticmethod
    def write_localversion() -> None:
        with open("localversion", "w", encoding="utf-8") as f:
            f.write("~zero_kernel")

    @property
    def _ucodename(self) -> str:
        return "dumplinger" if self.codename in ("dumpling", "cheeseburger") else self.codename

    @property
    def _defconfig(self) -> Path:
        defconfigs = {
            "los": "lineage_oneplus5_defconfig",
            "pa": "vendor/paranoid_defconfig" if self.lkv == "4.14" else "paranoid_defconfig",
            "x": "msm8998_oneplus_android_defconfig" if self.lkv == "4.14" else "oneplus5_defconfig"
        }
        # convert whatever output to path object
        return Path(defconfigs[self.base])

    def clean_build(self) -> None:
        print("\n", end="")
        msg.note("Cleaning the build environment..")
        cm.git(self.rm.paths[self.codename])
        cm.git(self.rm.paths["AnyKernel3"])
        cm.git(self.rm.paths["KernelSU"])
        for fn in os.listdir():
            if fn == "localversion" or fn.endswith(".zip"):
                cm.remove(fn)
        msg.done("Done!")

    def patch_strict_prototypes(self) -> None:
        msg.note("Patching sources for Clang 15+ compatibility..")
        data = {
            self.rm.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagchar_core.c":
            ("void diag_ws_init()", "void diag_ws_on_notify()", "void diag_ws_release()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_mux.c":
            ("int diag_mux_init()", "void diag_mux_exit()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_memorydevice.c":
            ("void diag_md_open_all()", "void diag_md_close_all()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_dci.c":
            ("void diag_dci_wakeup_clients()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_bridge.c":
            ("void diagfwd_bridge_exit()", "uint16_t diag_get_remote_device_mask()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_mhi.c":
            ("int diag_mhi_init()", "void diag_mhi_exit()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "camera_v2" /\
            "common" /\
            "msm_camera_tz_util.c":
            ("struct qseecom_handle *msm_camera_tz_get_ta_handle()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "vidc" /\
            "msm_vidc_common.c":
            ("void msm_comm_handle_thermal_event()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("static int voice_svc_dummy_reg()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("void msm_bus_rpm_set_mt_mask()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "staging" /\
            "qca-wifi-host-cmn" /\
            "hif" /\
            "src" /\
            "ce" /\
            "ce_service.c":
            ("struct ce_ops *ce_services_legacy()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "staging" /\
            "qcacld-3.0" /\
            "core" /\
            "hdd" /\
            "src" /\
            "wlan_hdd_main.c":
            ("hdd_adapter_t *hdd_get_first_valid_adapter()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_mdp.c":
            ("struct irq_info *mdss_intr_line()",),

            self.rm.paths[self.codename] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_util.c":
            ("struct mdss_util_intf *mdss_get_util_intf()",)
        }
        # the following files are not present in 4.14
        if self._linux_kernel_version != "4.14":
            extra_non_414 = {
                self.rm.paths[self.codename] /\
                "drivers" /\
                "soc" /\
                "qcom" /\
                "qdsp6v2" /\
                "voice_svc.c":
                ("void msm_bus_rpm_set_mt_mask()", "static int voice_svc_dummy_reg()"),

                self.rm.paths[self.codename] /\
                "drivers" /\
                "thermal" /\
                "msm_thermal-dev.c":
                ("int msm_thermal_ioctl_init()", "void msm_thermal_ioctl_cleanup()",),
            }
            data.update(extra_non_414)
        # PA needs this, LineageOS does not
        if self.base == "pa":
            extra_pa = {
                self.rm.paths[self.codename] /\
                "drivers" /\
                "staging" /\
                "qca-wifi-host-cmn" /\
                "target_if" /\
                "core" /\
                "src" /\
                "target_if_main.c":
                ("struct target_if_ctx *target_if_get_ctx()",),

                self.rm.paths[self.codename] /\
                "drivers" /\
                "staging" /\
                "qca-wifi-host-cmn" /\
                "wlan_cfg" /\
                "wlan_cfg.c":
                ("struct wlan_cfg_dp_soc_ctxt *wlan_cfg_soc_attach()",),
            }
            data.update(extra_pa)
        # start the patching process
        contents = ""
        for fname, funcnames in data.items():
            with open(fname, "r", encoding="utf-8") as f:
                contents = f.read()
            # replace: "()" -> "(void)"
            for func in funcnames:
                contents = contents.replace(func, func.replace("()", "(void)"))
            with open(fname, "w") as f:
                f.write(contents)
        msg.done("Done!")

    def patch_anykernel3(self) -> None:
        cm.remove(self.rm.paths["AnyKernel3"] / "ramdisk")
        cm.remove(self.rm.paths["AnyKernel3"] / "models")
        fo.ucopy(
            dcfg.root / "builder" / "modifications" / self._ucodename / "anykernel3" / "ramdisk",
            self.rm.paths["AnyKernel3"] / "ramdisk"
        )
        fo.ucopy(
            dcfg.root / "builder" / "modifications" / self._ucodename / "anykernel3" / "anykernel.sh",
            self.rm.paths["AnyKernel3"] / "anykernel.sh"
        )

    def patch_rtl8812au_source_mod_v5642(self) -> None:
        # Makefile
        fo.replace_lines(
            Path("Makefile").absolute(),
            (
                "#EXTRA_CFLAGS += -Wno-parentheses-equality",
                "#EXTRA_CFLAGS += -Wno-pointer-bool-conversion",
                "$(MAKE) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) -C $(KSRC) M=$(shell pwd)  modules",
                "CONFIG_PLATFORM_I386_PC = y",
                "CONFIG_PLATFORM_ANDROID_ARM64 = n",
            ),
            (
                "EXTRA_CFLAGS += -Wno-parentheses-equality",
                "EXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-pragma-pack\nEXTRA_CFLAGS += -Wno-unused-variable",
                '$(MAKE) ARCH=$(ARCH) SUBARCH=$(ARCH) REAL_CC=${CC_DIR}/clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=$(CROSS_COMPILE) -C $(KSRC) M=$(shell pwd) O="$(KBUILD_OUTPUT)" modules',
                "CONFIG_PLATFORM_I386_PC = n",
                "CONFIG_PLATFORM_ANDROID_ARM64 = y\nCONFIG_CONCURRENT_MODE = n",
            )
        )
        # ioctl_cfg80211.h
        fo.replace_lines(
            Path("os_dep", "linux", "ioctl_cfg80211.h").absolute(),
            ("#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 26)) && (LINUX_VERSION_CODE < KERNEL_VERSION(4, 7, 0))",),
            ("#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 26)) && (LINUX_VERSION_CODE < KERNEL_VERSION(4, 4, 0))",)
        )
        # ioctl_cfg80211.c
        fo.replace_lines(
            Path("os_dep", "linux", "ioctl_cfg80211.c").absolute(),
            (
                "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_SHORT_PREAMBLE;",
                "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_SHORT_SLOT_TIME;",
                "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_CTS_PROT;",
                "sinfo->bss_param.flags |= STATION_INFO_BSS_PARAM_DTIM_PERIOD;",
            ),
            (
                "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_SHORT_PREAMBLE;",
                "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_SHORT_SLOT_TIME;",
                "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_CTS_PROT;",
                "sinfo->bss_param.flags |= NL80211_STA_BSS_PARAM_DTIM_PERIOD;",
            )
        )

    def patch_rtl8812au(self) -> None:
        # copy RTL8812AU sources into kernel sources
        msg.note("Adding RTL8812AU drivers into the kernel..")
        fo.ucopy(
            self.rm.paths["rtl8812au"],
            self.rm.paths[self.codename] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        # modify sources depending on driver version
        os.chdir(
            self.rm.paths[self.codename] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        self.patch_rtl8812au_source_mod_v5642()
        cm.remove(".git*")
        os.chdir(dcfg.root)
        # include the driver into build process
        makefile = self.rm.paths[self.codename] /\
                   "drivers" /\
                   "net" /\
                   "wireless" /\
                   "realtek" /\
                   "Makefile"
        kconfig = self.rm.paths[self.codename] /\
                  "drivers" /\
                  "net" /\
                  "wireless" /\
                  "Kconfig"
        defconfig = self.rm.paths[self.codename] /\
                    "arch" /\
                    "arm64" /\
                    "configs" /\
                    self._defconfig
        with open(makefile, "a", encoding="utf-8") as f:
            f.write("obj-$(CONFIG_88XXAU)		+= rtl8812au/")
        fo.insert_before_line(
            kconfig,
            "endif",
            "source \"drivers/net/wireless/realtek/rtl8812au/Kconfig\""
        )
        with open(defconfig, "a", encoding="utf-8") as f:
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

    def patch_ksu(self) -> None:
        msg.note("Adding KernelSU into the kernel..")
        # extract KSU_GIT_VERSION environment variable manually
        goback = Path.cwd()
        os.chdir(self.rm.paths["KernelSU"])
        os.environ["KSU_GIT_VERSION"] = str(
            # official formula documented in KernelSU's Makefile
            10000 + int(ccmd.launch("git rev-list --count HEAD", get_output=True)) + 200 # type: ignore
        )
        os.chdir(goback)
        makefile = self.rm.paths[self.codename] /\
                   "drivers" /\
                   "Makefile"
        kconfig = self.rm.paths[self.codename] /\
                  "drivers" /\
                  "Kconfig"
        # include into the build process via symlink
        os.symlink(
            self.rm.paths["KernelSU"] / "kernel",
            self.rm.paths[self.codename] /\
            "drivers" /\
            "kernelsu"
        )
        with open(makefile, "a", encoding="utf-8") as f:
            f.write("obj-$(CONFIG_KSU)		+= kernelsu/\n")
        fo.insert_before_line(
            kconfig,
            "endmenu",
            "source \"drivers/kernelsu/Kconfig\""
        )
        # either patch kernel or KernelSU sources, depending on Linux kernel version
        target_dir = dcfg.root / "KernelSU" if self._linux_kernel_version == "4.14" else self.rm.paths[self.codename]
        fo.ucopy(
            dcfg.root / "builder" / "modifications" / self._ucodename / self._linux_kernel_version / "kernelsu-compat.patch",
            target_dir
        )
        os.chdir(target_dir)
        fo.apply_patch("kernelsu-compat.patch")
        os.chdir(goback)
        # add configs into defconfig
        defconfig = self.rm.paths[self.codename] /\
                    "arch" /\
                    "arm64" /\
                    "configs" /\
                    self._defconfig
        with open(defconfig, "a", encoding="utf-8") as f:
            extra_configs = (
                "CONFIG_KSU=y",
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

    def patch_qcacld(self) -> None:
        goback = Path.cwd()
        fo.ucopy(
            dcfg.root / "builder" / "modifications" / self._ucodename / self._linux_kernel_version / "qcacld_pa.patch",
            self.rm.paths[self.codename]
        )
        os.chdir(self.rm.paths[self.codename])
        fo.apply_patch("qcacld_pa.patch")
        os.chdir(goback)

    def patch_ioctl(self) -> None:
        ioctl = self.rm.paths[self.codename] /\
                "drivers" /\
                "platform" /\
                "msm" /\
                "ipa" /\
                "ipa_v3" /\
                "ipa.c"
        fo.replace_lines(
            ioctl.absolute(),
            ("	u8 header[128] = { 0 };",),
            ("	u8 header[512] = { 0 };",),
        )

    def patch_kernel(self) -> None:
        # -Wstrict-prototypes patch to build with Clang 15+
        clang_cmd = f'{self.rm.paths["clang"] / "bin" / "clang"} --version'
        clang_ver = str(ccmd.launch(clang_cmd, get_output=True)).split("clang version ")[1].split(".")[0]
        if int(clang_ver) >= 15:
            self.patch_strict_prototypes()
        # apply .patch files
        fo.ucopy(
            dcfg.root / "builder" / "modifications" / self._ucodename / self._linux_kernel_version,
            self.rm.paths[self.codename],
            ("kernelsu-compat.patch", "qcacld_pa.patch")
        )
        os.chdir(self.rm.paths[self.codename])
        for pf in Path.cwd().glob("*.patch"):
            fo.apply_patch(pf)
        # add support for CONFIG_MAC80211 kernel option
        data = ""
        files = ("tx.c", "mlme.c")
        for fn in files:
            with open(Path("net", "mac80211", fn), "r", encoding="utf-8") as f:
                data = f.read().replace("case IEEE80211_BAND_60GHZ:", "case NL80211_BAND_60GHZ:")
            with open(Path("net", "mac80211", fn), "w", encoding="utf-8") as f:
                f.write(data)
        # some patches only for ParanoidAndroid
        if self.base == "pa":
            if self._linux_kernel_version == "4.4":
                self.patch_qcacld()
            self.patch_ioctl()
        os.chdir(dcfg.root)

    def patch_all(self) -> None:
        self.patch_anykernel3()
        self.patch_kernel()
        # optionally include KernelSU support
        if self.ksu:
            self.patch_ksu()
        self.patch_rtl8812au()
        msg.done("Patches added!")

    def build(self) -> None:
        print("\n", end="")
        msg.note("Launching the build..")
        os.chdir(self.rm.paths[self.codename])
        # launch "make"
        punits = ccmd.launch("nproc --all", get_output=True)
        cmd1 = "make -j{} O=out {} "\
               "ARCH=arm64 "\
               "SUBARCH=arm64 "\
               "LLVM=1 "\
               "LLVM_IAS=1"\
                .format(punits, self._defconfig)
        cmd2 = "make -j{} O=out "\
               "ARCH=arm64 "\
               "SUBARCH=arm64 "\
               "CROSS_COMPILE=llvm- "\
               "CROSS_COMPILE_ARM32=arm-linux-androideabi- "\
               "CLANG_TRIPLE=aarch64-linux-gnu- "\
               "LLVM=1 "\
               "LLVM_IAS=1 "\
               "CXX=clang++ "\
               "AS=llvm-as"\
                .format(punits)
        # for PA's 4.14, extend the "make" command with additional variables
        if self.base == "pa" and self._linux_kernel_version == "4.14":
            cmd2 = f"{cmd2} LEX=flex YACC=bison"
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

    @property
    def _linux_kernel_version(self) -> str:
        data = ""
        version = []
        with open(self.rm.paths[self.codename] / "Makefile", encoding="utf-8") as f:
            data = f.read()
        params = ("VERSION", "PATCHLEVEL")
        # find the required lines in a single data run-through
        for line in data.splitlines():
            for p in params:
                if line.split(" =")[0] == p:
                    version.append(line.split(f"{p} = ")[1])
            # stop the loop when all values are found
            if len(version) == len(params):
                break
        return ".".join(version)

    def create_zip(self) -> None:
        print("\n", end="")
        msg.note("Forming final ZIP file..")
        fo.ucopy(
            self.rm.paths[self.codename] /\
            "out" /\
            "arch" /\
            "arm64" /\
            "boot" /\
            "Image.gz-dtb",
            self.rm.paths["AnyKernel3"] / "Image.gz-dtb"
        )
        # define kernel versions: Linux and internal
        verbase = self._linux_kernel_version
        ver_int = os.getenv("KVERSION")
        # create the final ZIP file
        name_suffix = "-ksu" if self.ksu else ""
        name_full = f"{os.getenv('KNAME', 'zero')}-{ver_int}-{self._ucodename}-{self.base}-{verbase}{name_suffix}"
        kdir = dcfg.root / dcfg.kernel
        if not kdir.is_dir():
            os.makedirs(kdir)
        os.chdir(self.rm.paths["AnyKernel3"])
        # this is not the best solution, but is the easiest
        cmd = f"zip -r9 {kdir / name_full}.zip . -x *.git* *README* *LICENSE* *placeholder"
        ccmd.launch(cmd)
        os.chdir(dcfg.root)
        msg.done("Done!")

    def run(self) -> None:
        os.chdir(dcfg.root)
        msg.banner("zero kernel builder")
        msg.note("Setting up tools and links..")
        self.rm.read_data()
        self.rm.generate_paths()
        self.rm.download()
        self.rm.export_path()
        self.clean_build()
        if self.clean_kernel:
            sys.exit(0)
        self.write_localversion()
        msg.done("Done! Tools are configured!")
        if self.lkv != self._linux_kernel_version:
            msg.error("Linux kernel version in sources is different what was specified in arguments")
        self.patch_all()
        self.build()
        self.create_zip()
