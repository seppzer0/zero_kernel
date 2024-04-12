from pathlib import Path
from abc import ABC, abstractmethod


class IContainerEngine(ABC):
    """An interface for ContainerEngine."""

    @property
    @abstractmethod
    def dir_bundle_conan(self) -> Path:
        """Determine path to Conan's local cache."""
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
    def build_image(self) -> None:
        """Build the image."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def run_cmd(self) -> str:
        """Form command for container launch."""
        raise NotImplementedError()

    @abstractmethod
    def __enter__(self) -> None:
        """Magic method for preparing the containerized build."""
        raise NotImplementedError()

    @abstractmethod
    def __exit__(self) -> None:
        """Magic method for post-build operations for the container engine."""
        raise NotImplementedError()


class IDockerEngine(ABC):
    """An interface for Docker-specific operations."""

    @staticmethod
    @abstractmethod
    def _force_buildkit() -> None:
        """Force enable Docker BuildKit."""
        raise NotImplementedError()

    @abstractmethod
    def _check_cache(self) -> bool:
        """Check local Docker cache for the specified image."""
        raise NotImplementedError()
