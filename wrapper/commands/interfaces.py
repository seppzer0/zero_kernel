from pathlib import Path
from abc import ABC, abstractmethod

from wrapper.clients import LineageOsApi, ParanoidAndroidApi

class IKernelBuilder(ABC):
    """An interface for the kernel builder."""

    @abstractmethod
    def __init__(self, **kwargs) -> None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _write_localversion() -> None:
        """Write a localversion file."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def _ucodename(self) -> str:
        """A unified device codename to apply patches for.

        E.g., "dumplinger", combining "dumpling" and "cheeseburger",
        both of which share the same kernel source.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def _defconfig(self) -> Path:
        """Determine defconfig file name.

        Depending on Linux kernel version (4.4 or 4.14)
        the location for defconfig file may vary.
        """
        raise NotImplementedError()

    @abstractmethod
    def _clean_build(self) -> None:
        """Clean environment from potential artifacts."""
        raise NotImplementedError()

    @abstractmethod
    def _patch_strict_prototypes(self) -> None:
        """A patcher to add compatibility with Clang 15 '-Wstrict-prototype' mandatory rule."""
        raise NotImplementedError()

    @abstractmethod
    def _patch_anykernel3(self) -> None:
        """Patch AnyKernel3 sources."""
        raise NotImplementedError()

    @abstractmethod
    def _patch_rtl8812au_source_mod_v5642(self) -> None:
        """Modifications specific to v5.6.4.2 driver version."""
        raise NotImplementedError()

    @abstractmethod
    def _patch_rtl8812au(self) -> None:
        """Patch RTL8812AU sources.

        NOTE: .patch files are unreliable in this case, have to replace lines manually
        """
        raise NotImplementedError()

    @abstractmethod
    def _patch_ksu(self) -> None:
        """Patch KernelSU into the kernel.

        During this process, a symlink is used to "place" KernelSU
        source into the kernel sources. This is due to the fact that KernelSU
        has an internal mechanism of getting it's version via accessing
        .git data. And having .git data in kernel sources is not ideal.
        """
        raise NotImplementedError()

    @abstractmethod
    def _patch_qcacld(self) -> None:
        """Patch QCACLD-3.0 defconfig to add support for monitor mode.

        Currently, this is required only for ParanoidAndroid.
        """
        raise NotImplementedError()

    @abstractmethod
    def _patch_ioctl(self) -> None:
        """Patch IOCTL buffer allocation."""
        raise NotImplementedError()

    @abstractmethod
    def _patch_kernel(self) -> None:
        """Patch kernel sources.

        Here only unrelated to KernelSU patches are applied.
        For applying KernelSU changes to kernel source see "patch_ksu()".
        """
        raise NotImplementedError()

    @abstractmethod
    def _patch_all(self) -> None:
        """Apply all patches."""
        raise NotImplementedError()

    @abstractmethod
    def _build(self) -> None:
        """Build the kernel."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def _linux_kernel_version(self) -> str:
        """Extract Linux kernel version number from sources."""
        raise NotImplementedError()

    @abstractmethod
    def _create_zip(self) -> None:
        """Pack build artifacts into a .zip archive."""
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
         """Execute the kernel builder logic."""
         raise NotImplementedError()

class IAssetsCollector(ABC):
    """An interface for the assets collector."""

    @property
    @abstractmethod
    def rom_collector_dto(self) -> LineageOsApi | ParanoidAndroidApi | None:
        """Determine the ROM for collection."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def assets(self) -> list[str | LineageOsApi | ParanoidAndroidApi]:
        """Form the full list of assets for collections."""
        raise NotImplementedError()

    @abstractmethod
    def _check(self) -> None:
        """Initiate some checks before execution."""
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        """Execute assets collector logic."""
        raise NotImplementedError()


class IBundleCreator(ABC):
    """An interface for the bundle creator."""

    @abstractmethod
    def _build_kernel(self, rom_name: str, clean_only: bool = False) -> None:
        """Build the kernel.

        :param rom_name: Name of the ROM.
        :param clean_only: Append an argument to just clean the kernel directory.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def _rom_only_flag(self) -> bool:
        """Determine the value of the --rom-only flag."""
        raise NotImplementedError()

    @abstractmethod
    def _collect_assets(self, rom_name: str, chroot: str) -> None:
        """Collect assets.

        :param rom_name: Name of the ROM.
        :param chroot: Type of chroot.
        """
        raise NotImplementedError()

    @abstractmethod
    def _conan_sources(self) -> None:
        """Prepare sources for rebuildable Conan packages."""
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _conan_options(json_file: str) -> dict:
        """Read Conan options from a JSON file.

        :param json_file: Name of the JSON file to read data from.
        """
        raise NotImplementedError()

    @abstractmethod
    def _conan_package(self, options: list[str], reference: str) -> None:
        """Create the Conan package.

        :param options: Conan options.
        :param reference: Conan reference.
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _conan_upload(reference: str) -> None:
        """Upload Conan component to the remote.

        :param reference: Conan reference.
        """
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
         """Execute the bundle creator logic."""
         raise NotImplementedError()
