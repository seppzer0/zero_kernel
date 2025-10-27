import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from zkb.tools import cleaning as cm, commands as ccmd, fileoperations as fo, banner
from zkb.configs import DirectoryConfig as dcfg
from zkb.managers import ResourceManager
from zkb.interfaces import IKernelBuilder


log = logging.getLogger("ZeroKernelLogger")


class KernelBuilder(BaseModel, IKernelBuilder):
    """Kernel builder.

    :param str codename: Device codename.
    :param str base: Kernel source base.
    :param str lkv: Linux kernel version.
    :param bool clean_kernel: Flag to clean folder with kernel sources.
    :param bool ksu: Flag indicating KernelSU support.
    :param Optional[Path]=None defconfig: Path to custom defconfig.
    """

    codename: str
    base: str
    lkv: str
    clean_kernel: bool
    ksu: bool
    rmanager: ResourceManager
    defconfig: Optional[Path] = None

    @staticmethod
    def write_localversion() -> None:
        with open("localversion", "w", encoding="utf-8") as f:
            f.write("~zero_kernel")

    @property
    def _ucodename(self) -> str:
        """Define unified codename for devices series with same kernels.

        :return: Unified codename.
        :rtype: str
        """
        if self.codename in ("dumpling", "cheeseburger"):
            return "dumplinger"
        elif "guacamole" in self.codename:
            return "guacamoles"
        else:
            return self.codename

    @property
    def _defconfig(self) -> Path:
        """Define defconfig.

        :return: Path to defconfig.
        :rtype: Path
        """
        # return custom defconfig if it is specified
        if self.defconfig:
            return Path(self.defconfig.name)

        # list of the available defconfigs
        op7_defconfigs = {
            "los": "lineage_sm8150_defconfig",
        }
        op5_defconfigs = {
            "los": "lineage_oneplus5_defconfig",
            "pa": "vendor/paranoid_defconfig" if self.lkv == "4.14" else "paranoid_defconfig",
            "x": "msm8998_oneplus_android_defconfig" if self.lkv == "4.14" else "oneplus5_defconfig"
        }

        # convert output to path object
        if "guacamole" in self.codename:
            return Path(op7_defconfigs[self.base])
        elif self.codename in ("dumpling", "cheeseburger"):
            return Path(op5_defconfigs[self.base])
        else:
            return Path()

    def clean_build(self) -> None:
        print("\n", end="")
        log.warning("Cleaning the build environment..")

        cm.git(self.rmanager.paths[self.codename])
        cm.git(self.rmanager.paths["AnyKernel3"])
        cm.git(self.rmanager.paths["KernelSU"])

        for fn in os.listdir():
            if fn == "localversion" or fn.endswith(".zip"):
                cm.remove(fn)

        log.info("Done!")

    def patch_strict_prototypes(self) -> None:
        log.warning("Patching sources for Clang 15+ compatibility..")

        data = {
            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagchar_core.c":
            ("void diag_ws_init()", "void diag_ws_on_notify()", "void diag_ws_release()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_mux.c":
            ("int diag_mux_init()", "void diag_mux_exit()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_memorydevice.c":
            ("void diag_md_open_all()", "void diag_md_close_all()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diag_dci.c":
            ("void diag_dci_wakeup_clients()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_bridge.c":
            ("void diagfwd_bridge_exit()", "uint16_t diag_get_remote_device_mask()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "char" /\
            "diag" /\
            "diagfwd_mhi.c":
            ("int diag_mhi_init()", "void diag_mhi_exit()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "camera_v2" /\
            "common" /\
            "msm_camera_tz_util.c":
            ("struct qseecom_handle *msm_camera_tz_get_ta_handle()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "media" /\
            "platform" /\
            "msm" /\
            "vidc" /\
            "msm_vidc_common.c":
            ("void msm_comm_handle_thermal_event()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("static int voice_svc_dummy_reg()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "soc" /\
            "qcom" /\
            "msm_bus" /\
            "msm_bus_rpm_smd.c":
            ("void msm_bus_rpm_set_mt_mask()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "staging" /\
            "qca-wifi-host-cmn" /\
            "hif" /\
            "src" /\
            "ce" /\
            "ce_service.c":
            ("struct ce_ops *ce_services_legacy()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "staging" /\
            "qcacld-3.0" /\
            "core" /\
            "hdd" /\
            "src" /\
            "wlan_hdd_main.c":
            ("hdd_adapter_t *hdd_get_first_valid_adapter()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_mdp.c":
            ("struct irq_info *mdss_intr_line()",),

            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "video" /\
            "fbdev" /\
            "msm" /\
            "mdss_util.c":
            ("struct mdss_util_intf *mdss_get_util_intf()",)
        }

        # the following files are not present in 4.14
        if self.lkv_src != "4.14":
            extra_non_414 = {
                self.rmanager.paths[self.codename] /\
                "drivers" /\
                "soc" /\
                "qcom" /\
                "qdsp6v2" /\
                "voice_svc.c":
                ("void msm_bus_rpm_set_mt_mask()", "static int voice_svc_dummy_reg()"),

                self.rmanager.paths[self.codename] /\
                "drivers" /\
                "thermal" /\
                "msm_thermal-dev.c":
                ("int msm_thermal_ioctl_init()", "void msm_thermal_ioctl_cleanup()",),
            }
            data.update(extra_non_414)

        # PA needs this, LineageOS does not
        if self.base == "pa":
            extra_pa = {
                self.rmanager.paths[self.codename] /\
                "drivers" /\
                "staging" /\
                "qca-wifi-host-cmn" /\
                "target_if" /\
                "core" /\
                "src" /\
                "target_if_main.c":
                ("struct target_if_ctx *target_if_get_ctx()",),

                self.rmanager.paths[self.codename] /\
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
            for func in funcnames:
                contents = contents.replace(func, func.replace("()", "(void)"))
            with open(fname, "w") as f:
                f.write(contents)

        log.info("Done!")

    def patch_anykernel3(self) -> None:
        cm.remove(self.rmanager.paths["AnyKernel3"] / "ramdisk")
        cm.remove(self.rmanager.paths["AnyKernel3"] / "models")

        #fo.ucopy(
        #    dcfg.root / "zkb" / "modifications" / self._ucodename / "anykernel3" / "ramdisk",
        #    self.rmanager.paths["AnyKernel3"] / "ramdisk"
        #)
        fo.ucopy(
            dcfg.root / "zkb" / "modifications" / self._ucodename / "anykernel3" / "anykernel.sh",
            self.rmanager.paths["AnyKernel3"] / "anykernel.sh"
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
                "EXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-pointer-bool-conversion\nEXTRA_CFLAGS += -Wno-pragma-pack\nEXTRA_CFLAGS += -Wno-unused-variable", # noqa: E501
                '$(MAKE) ARCH=$(ARCH) SUBARCH=$(ARCH) REAL_CC=${CC_DIR}/clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=$(CROSS_COMPILE) -C $(KSRC) M=$(shell pwd) O="$(KBUILD_OUTPUT)" modules', # noqa: E501
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

    def update_defconfig(self) -> None:
        defconfig = self.rmanager.paths[self.codename] /\
                    "arch" /\
                    "arm64" /\
                    "configs" /\
                    self._defconfig

        # base changes (Wi-Fi + RTL8812AU)
        extra_configs = [
                "CONFIG_88XXAU=y",
                "CONFIG_MODULE_FORCE_LOAD=y",
                "CONFIG_MODULE_FORCE_UNLOAD=y",
                "CONFIG_CFG80211_WEXT=y",
                "CONFIG_CFG80211_WEXT_EXPORT=y",
                "CONFIG_CONCURRENT_MODE=n",
                "CONFIG_MAC80211=y",
                "CONFIG_RTL8187=y",
                "CONFIG_RTLWIFI=y",
            ]

        # KernelSU changes
        if self.ksu:
            extra_configs.extend([
                "CONFIG_KSU=y",
                "CONFIG_MODULES=y",
                "CONFIG_MODULE_UNLOAD=y",
                "CONFIG_MODVERSIONS=y",
                "CONFIG_DIAG_CHAR=y",
                "CONFIG_KPROBES=y",
                "CONFIG_HAVE_KPROBES=y",
                "CONFIG_KPROBE_EVENTS=y",
            ])

        # apply changes
        with open(defconfig, "a", encoding="utf-8") as f:
            f.write("\n".join(extra_configs))
            f.write("\n")

    def patch_rtl8812au(self) -> None:
        # copy RTL8812AU sources into kernel sources
        log.warning("Adding RTL8812AU drivers into the kernel..")
        fo.ucopy(
            self.rmanager.paths["rtl8812au"],
            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "net" /\
            "wireless" /\
            "realtek" /\
            "rtl8812au"
        )

        # modify sources depending on driver version
        os.chdir(
            self.rmanager.paths[self.codename] /\
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
        makefile = self.rmanager.paths[self.codename] /\
                   "drivers" /\
                   "net" /\
                   "wireless" /\
                   "realtek" /\
                   "Makefile"
        kconfig = self.rmanager.paths[self.codename] /\
                  "drivers" /\
                  "net" /\
                  "wireless" /\
                  "Kconfig"
        with open(makefile, "a", encoding="utf-8") as f:
            f.write("obj-$(CONFIG_88XXAU)		+= rtl8812au/")
        fo.insert_before_line(
            kconfig,
            "endif",
            'source "drivers/net/wireless/realtek/rtl8812au/Kconfig"'
        )

    def patch_ksu(self) -> None:
        log.warning("Adding KernelSU into the kernel..")

        patch_name = "kernelsu-compat.patch"

        # extract KSU version manually and include it via symlink
        goback = Path.cwd()
        os.chdir(self.rmanager.paths["KernelSU"])
        os.environ["KSU_GIT_VERSION"] = str(
            # official formula documented in KernelSU's Makefile
            10000 + int(ccmd.launch("git rev-list --count HEAD", get_output=True)) + 200 # type: ignore
        )
        os.chdir(goback)

        makefile = self.rmanager.paths[self.codename] /\
                   "drivers" /\
                   "Makefile"
        kconfig = self.rmanager.paths[self.codename] /\
                  "drivers" /\
                  "Kconfig"

        os.symlink(
            self.rmanager.paths["KernelSU"] / "kernel",
            self.rmanager.paths[self.codename] /\
            "drivers" /\
            "kernelsu"
        )

        with open(makefile, "a", encoding="utf-8") as f:
            f.write("obj-$(CONFIG_KSU)		+= kernelsu/\n")
        fo.insert_before_line(
            kconfig,
            "endmenu",
            'source "drivers/kernelsu/Kconfig"'
        )

        # either patch kernel or KernelSU sources, depending on Linux kernel version
        target_d = dcfg.root / "KernelSU" if self.lkv_src == "4.14" else self.rmanager.paths[self.codename]
        fo.ucopy(
            dcfg.root / "zkb" / "modifications" / self._ucodename / self.lkv_src / patch_name,
            target_d
        )
        os.chdir(target_d)
        fo.apply_patch(patch_name)
        os.chdir(goback)

    def patch_qcacld(self) -> None:
        patch_name = "qcacld_pa.patch"

        goback = Path.cwd()

        fo.ucopy(
            dcfg.root / "zkb" / "modifications" / self._ucodename / self.lkv_src / patch_name,
            self.rmanager.paths[self.codename]
        )
        os.chdir(self.rmanager.paths[self.codename])

        fo.apply_patch(patch_name)
        os.chdir(goback)

    def patch_ioctl(self) -> None:
        ioctl = self.rmanager.paths[self.codename] /\
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
        clang_cmd = f'{self.rmanager.paths["clang"] / "bin" / "clang"} --version'
        clang_ver = str(ccmd.launch(clang_cmd, get_output=True)).split("clang version ")[1].split(".")[0]

        if int(clang_ver) >= 15:
            self.patch_strict_prototypes()

        # apply .patch files
        fo.ucopy(
            dcfg.root / "zkb" / "modifications" / self._ucodename / self.lkv_src,
            self.rmanager.paths[self.codename],
            ("kernelsu-compat.patch", "qcacld_pa.patch")
        )
        os.chdir(self.rmanager.paths[self.codename])

        for pf in Path.cwd().glob("*.patch"):
            # TODO: adjust exceptions after testing if needed
            #exceptions = (
            #    "fix-hci-uart.patch",
            #    "fix-rt2800-injection-4.04.patch",
            #)
            #if pf not in exceptions:
            fo.apply_patch(pf)

        # add support for CONFIG_MAC80211 kernel option
        data = ""
        files = ("tx.c", "mlme.c")

        os.chdir(self.rmanager.paths[self.codename])

        for fn in files:
            f_path = self.rmanager.paths[self.codename] / "net" / "mac80211" / fn
            if f_path.is_file():
                with open(f_path, "r", encoding="utf-8") as f:
                    data = f.read().replace("case IEEE80211_BAND_60GHZ:", "case NL80211_BAND_60GHZ:")
                with open(f_path, "w", encoding="utf-8") as f:
                    f.write(data)
            else:
                log.warning(f"Modification of {str(f_path)} is skipped")

        # some patches only for ParanoidAndroid
        if self.base == "pa":
            if self.lkv_src == "4.4":
                self.patch_qcacld()
            #self.patch_ioctl()

        os.chdir(dcfg.root)

    def patch_all(self) -> None:
        self.patch_anykernel3()
        self.patch_kernel()

        # optionally include KernelSU support
        if self.ksu:
            self.patch_ksu()

        # NOTE: Disabled in favour of new drivers from rtw88
        #self.patch_rtl8812au()

        if self.defconfig:
            log.warning("Custom defconfig provided, copying..")
            fo.ucopy(
                self.defconfig,
                self.rmanager.paths[self.codename] /\
                "arch" /\
                "arm64" /\
                "configs" /\
                self._defconfig
            )
        else:
            self.update_defconfig()

        log.info("Patches added!")

    def build(self) -> None:
        print("\n", end="")
        log.warning("Launching the build..")

        os.chdir(self.rmanager.paths[self.codename])

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
        if (self.base, self.lkv_src) == ("pa", "4.14"):
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

        log.info("Done! Time spent for the build: %02d:%02d:%02d" % (hours, mins, secs))

    @property
    def lkv_src(self) -> str:
        """Linux kernel version in kernel source.

        :return: Linux kernel version found in sources.
        :rtype: str
        """
        data = ""
        version = []

        with open(self.rmanager.paths[self.codename] / "Makefile", encoding="utf-8") as f:
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
        log.warning("Forming final ZIP file..")

        fo.ucopy(
            self.rmanager.paths[self.codename] /\
            "out" /\
            "arch" /\
            "arm64" /\
            "boot" /\
            "Image.gz-dtb",
            self.rmanager.paths["AnyKernel3"] / "Image.gz-dtb"
        )

        # define kernel versions: Linux and internal
        verbase = self.lkv_src
        ver_int = os.getenv("KVERSION")

        # create the final ZIP file
        name_suffix = "-ksu" if self.ksu else ""
        name_full = f'{os.getenv("KNAME", "zero")}-{ver_int}-{self._ucodename}-{self.base}-{verbase}{name_suffix}'
        kdir = dcfg.root / dcfg.kernel

        if not kdir.is_dir():
            os.makedirs(kdir)

        os.chdir(self.rmanager.paths["AnyKernel3"])

        # this is not the best solution, but is the easiest
        cmd = f"zip -r9 {kdir / name_full}.zip . -x *.git* *README* *LICENSE* *placeholder"
        ccmd.launch(cmd)
        os.chdir(dcfg.root)

        log.info("Done!")

    def run(self) -> None:
        os.chdir(dcfg.root)
        banner.print_banner("zero kernel builder")
        log.warning("Setting up tools and links..")

        self.rmanager.read_data()
        self.rmanager.generate_paths()
        self.rmanager.download()
        self.rmanager.export_path()
        self.clean_build()

        if self.clean_kernel:
            sys.exit(0)

        self.write_localversion()
        log.info("Done! Tools are configured!")

        if self.lkv != self.lkv_src:
            log.error("Linux kernel version in sources is different what was specified in arguments")
            sys.exit(1)

        self.patch_all()
        self.build()
        self.create_zip()
