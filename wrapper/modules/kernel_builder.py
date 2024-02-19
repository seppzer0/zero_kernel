import os
import sys
import time
from pathlib import Path
from pydantic import BaseModel

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg
import wrapper.tools.commands as ccmd
import wrapper.tools.fileoperations as fo

from wrapper.configs.directory_config import DirectoryConfig as dcfg

from wrapper.utils import ResourceManager

from wrapper.modules.interfaces import IModuleExecutor


class KernelBuilder(BaseModel, IModuleExecutor):
    """Kernel builder.

    :param codename: Device codename.
    :param base: Kernel source base.
    :param lkv: Linux kernel version.
    :param clean_kernel: Flag to clean folder with kernel sources.
    :param ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    lkv: str
    clean_kernel: bool
    ksu: bool

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._rcs = ResourceManager(codename=self.codename, base=self.base, lkv=self.lkv)

    def run(self) -> None:
        os.chdir(dcfg.root)
        msg.banner("zero kernel builder")
        msg.note("Setting up tools and links..")
        self._rcs.path_gen()
        self._rcs.download()
        self._rcs.export_path()
        self._clean_build()
        if self.clean_kernel:
            sys.exit(0)
        self._write_localversion()
        msg.done("Done! Tools are configured!")
        if self.lkv != self._linux_kernel_version:
            msg.error("Linux kernel version in sources is different what was specified in arguments")
        self._patch_all()
        self._build()
        self._create_zip()

    @staticmethod
    def _write_localversion() -> None:
        """Write a localversion file."""
        with open("localversion", "w") as f:
            f.write("~zero-kernel")

    @property
    def _ucodename(self) -> str:
        """A unified device codename to apply patches for.

        E.g., "dumplinger", combining "dumpling" and "cheeseburger",
        both of which share the same kernel source.
        """
        return "dumplinger" if self.codename in ("dumpling", "cheeseburger") else self.codename

    @property
    def _defconfig(self) -> Path:
        """Determine defconfig file name.

        Depending on Linux kernel version (4.4 or 4.14)
        the location for defconfig file may vary.
        """
        defconfigs = {
            "los": Path("lineage_oneplus5_defconfig"),
            "pa": Path("vendor", "paranoid_defconfig") if self.lkv == "4.14" else Path("paranoid_defconfig"),
            "x": Path("msm8998_oneplus_android_defconfig") if self.lkv == "4.14" else Path("oneplus5_defconfig")
        }
        return defconfigs[self.base]

    def _clean_build(self) -> None:
        """Clean environment from potential artifacts."""
        print("\n", end="")
        msg.note("Cleaning the build environment..")
        cm.git(self._rcs.paths[self.codename]["path"])
        cm.git(self._rcs.paths["AnyKernel3"]["path"])
        cm.git(self._rcs.paths["KernelSU"]["path"])
        for fn in os.listdir():
            if fn == "localversion" or fn.endswith(".zip"):
                cm.remove(fn)
        msg.done("Done!")

    def _patch_strict_prototypes(self) -> None:
        """A patcher to add compatibility with Clang 15 '-Wstrict-prototype' mandatory rule."""
        msg.note("Patching sources for Clang 15+ compatibility..")
        data = {
            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagchar_core.c":
            ("void diag_ws_init()", "void diag_ws_on_notify()", "void diag_ws_release()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_mux.c":
            ("int diag_mux_init()", "void diag_mux_exit()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_memorydevice.c":
            ("void diag_md_open_all()", "void diag_md_close_all()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_dci.c":
            ("void diag_dci_wakeup_clients()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_bridge.c":
            ("void diagfwd_bridge_exit()", "uint16_t diag_get_remote_device_mask()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_mhi.c":
            ("int diag_mhi_init()", "void diag_mhi_exit()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "camera_v2" /\
            "common" /\
            "msm_camera_tz_util.c":
            ("struct qseecom_handle *msm_camera_tz_get_ta_handle()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "vidc" /\
            "msm_vidc_common.c":
            ("void msm_comm_handle_thermal_event()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("static int voice_svc_dummy_reg()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("void msm_bus_rpm_set_mt_mask()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "staging" /\
            "qca-wifi-host-cmn" /\
            "hif" /\
            "src" /\
            "ce" /\
            "ce_service.c":
            ("struct ce_ops *ce_services_legacy()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "staging" /\
            "qcacld-3.0" /\
            "core" /\
            "hdd" /\
            "src" /\
            "wlan_hdd_main.c":
            ("hdd_adapter_t *hdd_get_first_valid_adapter()",),

            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_mdp.c":
            ("struct irq_info *mdss_intr_line()",),

            self._rcs.paths[self.codename]["path"] /\
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
                self._rcs.paths[self.codename]["path"] /\
                "drivers" /\
                "soc" /\
                "qcom" /\
                "qdsp6v2" /\
                "voice_svc.c":
                ("void msm_bus_rpm_set_mt_mask()", "static int voice_svc_dummy_reg()"),

                self._rcs.paths[self.codename]["path"] /\
                "drivers" /\
                "thermal" /\
                "msm_thermal-dev.c":
                ("int msm_thermal_ioctl_init()", "void msm_thermal_ioctl_cleanup()",),
            }
            data.update(extra_non_414)
        # PA needs this, LineageOS does not
        if self.base == "pa":
            extra_pa = {
                self._rcs.paths[self.codename]["path"] /\
                "drivers" /\
                "staging" /\
                "qca-wifi-host-cmn" /\
                "target_if" /\
                "core" /\
                "src" /\
                "target_if_main.c":
                ("struct target_if_ctx *target_if_get_ctx()",),

                self._rcs.paths[self.codename]["path"] /\
                "drivers" /\
                "staging" /\
                "qca-wifi-host-cmn" /\
                "wlan_cfg" /\
                "wlan_dcfg.c":
                ("struct wlan_cfg_dp_soc_ctxt *wlan_cfg_soc_attach()",),
            }
            data.update(extra_pa)
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
            dcfg.root / "wrapper" / "modifications" / self._ucodename / "anykernel3" / "ramdisk",
            self._rcs.paths["AnyKernel3"]["path"] / "ramdisk"
        )
        fo.ucopy(
            dcfg.root / "wrapper" / "modifications" / self._ucodename / "anykernel3" / "anykernel.sh",
            self._rcs.paths["AnyKernel3"]["path"] / "anykernel.sh"
        )

    def _patch_rtl8812au_source_mod_v5642(self) -> None:
        """Modifications specific to v5.6.4.2 driver version."""
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

    def _patch_rtl8812au(self) -> None:
        """Patch RTL8812AU sources.

        NOTE: .patch files are unreliable in this case, have to replace lines manually
        """
        # copy RTL8812AU sources into kernel sources
        msg.note("Adding RTL8812AU drivers into the kernel..")
        fo.ucopy(
            self._rcs.paths["rtl8812au"]["path"],
            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        # modify sources depending on driver version
        os.chdir(
            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )
        self._patch_rtl8812au_source_mod_v5642()
        cm.remove(".git*")
        os.chdir(dcfg.root)
        # include the driver into build process
        makefile = self._rcs.paths[self.codename]["path"] /\
                   "drivers" /\
                   "net" /\
                   "wireless" /\
                   "realtek" /\
                   "Makefile"
        kconfig = self._rcs.paths[self.codename]["path"] /\
                  "drivers" /\
                  "net" /\
                  "wireless" /\
                  "Kconfig"
        defconfig = self._rcs.paths[self.codename]["path"] /\
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
        # extract KSU_GIT_VERSION environment variable manually
        goback = Path.cwd()
        os.chdir(self._rcs.paths["KernelSU"]["path"])
        os.environ["KSU_GIT_VERSION"] = str(
            # official formula documented in KernelSU's Makefile
            10000 + int(ccmd.launch("git rev-list --count HEAD", get_output=True)) + 200
        )
        os.chdir(goback)
        makefile = self._rcs.paths[self.codename]["path"] /\
                   "drivers" /\
                   "Makefile"
        kconfig = self._rcs.paths[self.codename]["path"] /\
                  "drivers" /\
                  "Kconfig"
        # include into the build process via symlink
        os.symlink(
            self._rcs.paths["KernelSU"]["path"] / "kernel",
            self._rcs.paths[self.codename]["path"] /\
            "drivers" /\
            "kernelsu"
        )
        with open(makefile, "a") as f:
            f.write("obj-$(CONFIG_KSU)		+= kernelsu/\n")
        fo.insert_before_line(
            kconfig,
            "endmenu",
            "source \"drivers/kernelsu/Kconfig\""
        )
        # either patch kernel or KernelSU sources, depending on Linux kernel version
        target_dir = dcfg.root / "KernelSU" if self._linux_kernel_version == "4.14" else self._rcs.paths[self.codename]["path"]
        fo.ucopy(
            dcfg.root / "wrapper" / "modifications" / self._ucodename / self._linux_kernel_version / "kernelsu-compat.patch",
            target_dir
        )
        os.chdir(target_dir)
        fo.apply_patch("kernelsu-compat.patch")
        os.chdir(goback)
        # add configs into defconfig
        defconfig = self._rcs.paths[self.codename]["path"] /\
                    "arch" /\
                    "arm64" /\
                    "configs" /\
                    self._defconfig
        with open(defconfig, "a") as f:
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

    def _patch_qcacld(self) -> None:
        """Patch QCACLD-3.0 defconfig to add support for monitor mode.

        Currently, this is required only for ParanoidAndroid.
        """
        goback = Path.cwd()
        fo.ucopy(
            dcfg.root / "wrapper" / "modifications" / self._ucodename / self._linux_kernel_version / "qcacld_pa.patch",
            self._rcs.paths[self.codename]["path"]
        )
        os.chdir(self._rcs.paths[self.codename]["path"])
        fo.apply_patch("qcacld_pa.patch")
        os.chdir(goback)

    def _patch_ioctl(self) -> None:
        """Patch IOCTL buffer allocation."""
        ioctl = self._rcs.paths[self.codename]["path"] /\
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

    def _patch_kernel(self) -> None:
        """Patch kernel sources.

        Here only unrelated to KernelSU patches are applied.
        For applying KernelSU changes to kernel source see "patch_ksu()".
        """
        # -Wstrict-prototypes patch to build with Clang 15+
        clang_cmd = f'{self._rcs.paths["clang"]["path"] / "bin" / "clang"} --version'
        clang_ver = ccmd.launch(clang_cmd, get_output=True).split("clang version ")[1].split(".")[0]
        if int(clang_ver) >= 15:
            self._patch_strict_prototypes()
        # apply .patch files
        fo.ucopy(
            dcfg.root / "wrapper" / "modifications" / self._ucodename / self._linux_kernel_version,
            self._rcs.paths[self.codename]["path"],
            ("kernelsu-compat.patch", "qcacld_pa.patch")
        )
        os.chdir(self._rcs.paths[self.codename]["path"])
        for pf in Path.cwd().glob("*.patch"):
            fo.apply_patch(pf)
        # add support for CONFIG_MAC80211 kernel option
        data = ""
        files = ("tx.c", "mlme.c")
        for fn in files:
            with open(Path("net", "mac80211", fn), "r") as f:
                data = f.read().replace("case IEEE80211_BAND_60GHZ:", "case NL80211_BAND_60GHZ:")
            with open(Path("net", "mac80211", fn), "w") as f:
                f.write(data)
        # some patches only for ParanoidAndroid
        if self.base == "pa":
            if self._linux_kernel_version == "4.4":
                self._patch_qcacld()
            self._patch_ioctl()
        os.chdir(dcfg.root)

    def _patch_all(self) -> None:
        """Apply all patches."""
        self._patch_anykernel3()
        self._patch_kernel()
        # optionally include KernelSU support
        if self.ksu:
            self._patch_ksu()
        self._patch_rtl8812au()
        msg.done("Patches added!")

    def _build(self) -> None:
        """Build the kernel."""
        print("\n", end="")
        msg.note("Launching the build..")
        os.chdir(self._rcs.paths[self.codename]["path"])
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
        """Extract Linux kernel version number from sources."""
        data = ""
        version = []
        with open(self._rcs.paths[self.codename]["path"] / "Makefile") as f:
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

    def _create_zip(self) -> None:
        """Pack build artifacts into a .zip archive."""
        print("\n", end="")
        msg.note("Forming final ZIP file..")
        fo.ucopy(
            self._rcs.paths[self.codename]["path"] /\
            "out" /\
            "arch" /\
            "arm64" /\
            "boot" /\
            "Image.gz-dtb",
            self._rcs.paths["AnyKernel3"]["path"] / "Image.gz-dtb"
        )
        # define kernel versions: Linux and internal
        verbase = self._linux_kernel_version
        ver_int = os.getenv("KVERSION")
        # create the final ZIP file
        name_suffix = "-ksu" if self.ksu else ""
        name_full = f"{os.getenv('KNAME', 'zero')}-{ver_int}-{self._ucodename}-{self.base}-{verbase}{name_suffix}"
        kdir = dcfg.root / dcfg.kernel
        if not kdir.is_dir():
            os.mkdir(kdir)
        os.chdir(self._rcs.paths["AnyKernel3"]["path"])
        # this is not the best solution, but is the easiest
        cmd = f"zip -r9 {kdir / name_full}.zip . -x *.git* *README* *LICENSE* *placeholder"
        ccmd.launch(cmd)
        os.chdir(dcfg.root)
        msg.done("Done!")
