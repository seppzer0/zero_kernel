from abc import ABC, abstractmethod


class IBundleCommand(ABC):
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
