from pathlib import Path
from abc import ABC, abstractmethod
from subprocess import CompletedProcess


class IGenericContainerEngine(ABC):
    """Interface for containerized builds."""

    @property
    @abstractmethod
    def dir_bundle_conan(self) -> Path:
        """Determine path to Conan's local cache."""
        raise NotImplementedError()

    @abstractmethod
    def check_cache(self) -> bool:
        """Check local cache for target image presence."""
        raise NotImplementedError()

    @property
    def builder_cmd(self) -> str:
        """Form the launch command for the builder."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def container_options(self) -> list[str]:
        """Form the options for container launch."""
        raise NotImplementedError()

    @abstractmethod
    def create_dirs(self) -> None:
        """Create key directories."""
        raise NotImplementedError()

    @abstractmethod
    def build_image(self) -> str | None | CompletedProcess:
        """Build the image."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def get_container_cmd(self) -> str:
        """Form command for container launch."""
        raise NotImplementedError()
