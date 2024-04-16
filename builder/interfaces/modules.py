from pathlib import Path
from abc import ABC, abstractmethod

from builder.clients import LineageOsApi, ParanoidAndroidApi


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
    def assets(self) -> tuple[str, str | None] | list[str] | None:
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
