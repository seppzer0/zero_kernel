from abc import ABC, abstractmethod

from zkb.clients import LineageOsApiClient, ParanoidAndroidApiClient


class IKernelBuilder(ABC):
    """Interface for the kernel builder."""

    @staticmethod
    @abstractmethod
    def write_localversion() -> None:
        """Write a .localversion file.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def clean_build(self) -> None:
        """Clean environment from potential artifacts.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_strict_prototypes(self) -> None:
        """Patch source to comply with Clang 15 '-Wstrict-prototype' rule.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_anykernel3(self) -> None:
        """Patch AnyKernel3 sources.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def update_defconfig(self) -> None:
        """Update defconfig file.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_rtl8812au_source_mod_v5642(self) -> None:
        """Modify the v5.6.4.2 version version of the driver.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_rtl8812au(self) -> None:
        """Patch RTL8812AU sources.

        NOTE: .patch files are unreliable in this case, have to replace lines manually.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_ksu(self) -> None:
        """Patch KernelSU into the kernel.

        During this process, a symlink is used to "place" KernelSU
        source into the kernel sources. This is due to the fact that KernelSU
        has an internal mechanism of getting it's version via accessing
        .git data. And having .git data in kernel sources is not ideal.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_qcacld(self) -> None:
        """Patch QCACLD-3.0 defconfig to add support for monitor mode.

        Currently, this is required only for ParanoidAndroid.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_ioctl(self) -> None:
        """Patch IOCTL buffer allocation.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_kernel(self) -> None:
        """Patch kernel sources.

        Here only unrelated to KernelSU patches are applied.
        For applying KernelSU changes to kernel source see "patch_ksu()".

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def patch_all(self) -> None:
        """Apply all patches.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def build(self) -> None:
        """Build the kernel.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def create_zip(self) -> None:
        """Pack build artifacts into a .zip archive.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
         """Execute the kernel builder logic.

         :return: None
         """
         raise NotImplementedError()


class IAssetsCollector(ABC):
    """Interface for the assets collector."""

    @property
    @abstractmethod
    def rom_collector_dto(self) -> LineageOsApiClient | ParanoidAndroidApiClient | None:
        """Determine the ROM for collection.

        :return: ROM API client instance if applicable.
        :rtype: LineageOsApiClient | ParanoidAndroidApiClient | None
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def assets(self) -> list:
        """Form the full list of assets for collections.

        :return: Data with assets to be collected.
        :rtype: list
        """
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        """Execute assets collector logic.

        :return: None
        """
        raise NotImplementedError()
