from typing import Literal
from abc import ABC, abstractmethod


class ICommand(ABC):
    """Interface for builder's commands."""

    @abstractmethod
    def execute(self) -> None:
        """Execute command's logic."""
        raise NotImplementedError()


class IBundleCommand(ABC):
    """Extended interface for the bundle formation."""

    @abstractmethod
    def build_kernel(self, rom_name: str, clean_only: bool) -> None:
        """Build the kernel.

        :param str rom_name: Name of the ROM.
        :param bool clean_only: Append an argument to just clean the kernel directory.
        """
        raise NotImplementedError()

    @abstractmethod
    def collect_assets(self, rom_name: str, chroot: Literal["full", "minimal"]) -> None:
        """Collect assets.

        :param str rom_name: Name of the ROM.
        :param Literal["full","minimal"] chroot: Type of chroot.
        """
        raise NotImplementedError()

    @abstractmethod
    def conan_sources(self) -> None:
        """Prepare sources for rebuildable Conan packages."""
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def conan_options(json_file: str) -> dict:
        """Read Conan options from a JSON file.

        :param str json_file: Name of the JSON file to read data from.
        """
        raise NotImplementedError()

    @abstractmethod
    def conan_package(self, options: tuple[str, ...], reference: str) -> None:
        """Create the Conan package.

        :param tuple[str,...] options: Conan options.
        :param str reference: Conan reference.
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def conan_upload(reference: str) -> None:
        """Upload Conan component to the remote.

        :param str reference: Conan reference.
        """
        raise NotImplementedError()
