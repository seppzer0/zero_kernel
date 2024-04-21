from pathlib import Path
from abc import ABC, abstractmethod
from subprocess import CompletedProcess


class IGenericContainerEngine(ABC):
    """An interface for GenericContainerEngine."""

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
        """Return the launch command for the builder."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def container_options(self) -> list[str]:
        """Form the arguments for container launch."""
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
    def run_cmd(self) -> str:
        """Form command for container launch."""
        raise NotImplementedError()

    @abstractmethod
    def __enter__(self) -> str:
        """Magic method for preparing the containerized build."""
        raise NotImplementedError()

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Magic method for post-build operations for the container engine."""
        raise NotImplementedError()
