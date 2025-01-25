from pathlib import Path
from abc import ABC, abstractmethod
from subprocess import CompletedProcess


class IGenericContainerEngine(ABC):
    """Interface for containerized builds."""

    @property
    @abstractmethod
    def dir_bundle_conan(self) -> Path:
        """Determine path to Conan's local cache.

        :return: Path to local Conan cache.
        :rtype: Path
        """
        raise NotImplementedError()

    @abstractmethod
    def check_cache(self) -> bool:
        """Check local cache for target image presence.

        :return: Indicator that target image is already in local cache.
        :rtype: bool
        """
        raise NotImplementedError()

    @property
    def builder_cmd(self) -> str:
        """Form the launch command for the builder.

        :return: Command to run.
        :rtype: str
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def container_options(self) -> list[str]:
        """Form the options for container launch.

        :return: Docker/Podman options for "run" command.
        :rtype: list[str]
        """
        raise NotImplementedError()

    @abstractmethod
    def create_dirs(self) -> None:
        """Create key directories.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def build_image(self) -> str | None | CompletedProcess:
        """Build the image.

        :return: Result of lauching image build.
        :rtype: str | None | CompletedProcess
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def get_container_cmd(self) -> str:
        """Form command for container launch.

        :return: Docker/Podman "run" command
        :rtype: str
        """
        raise NotImplementedError()
