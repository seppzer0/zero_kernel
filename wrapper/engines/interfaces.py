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
    def wrapper_cmd(self) -> str:
        """Return the launch command for the wrapper."""
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
    def build(self) -> None:
        """Build the image."""
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        """Execute the containerized build logic."""
        raise NotImplementedError()


class IDockerEngine(ABC):
    """An interface for Docker-specific methods."""

    @staticmethod
    @abstractmethod
    def _force_buildkit() -> None:
        """Force enable Docker BuildKit."""
        raise NotImplementedError()

    @abstractmethod
    def _check_cache(self) -> bool:
        """Check local Docker cache for the specified image."""
        raise NotImplementedError()
