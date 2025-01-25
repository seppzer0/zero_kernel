from abc import ABC, abstractmethod


class IResourceManager(ABC):
    """Interface for the resource manager."""

    @abstractmethod
    def read_data(self) -> None:
        """Read data from all of the JSON files.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def generate_paths(self) -> None:
        """Generate paths with Path objects.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def download(self) -> None:
        """Download files from URLs.

        :return: None
        """
        raise NotImplementedError()

    @abstractmethod
    def export_path(self) -> None:
        """Export path to PATH.

        :return: None
        """
        raise NotImplementedError()
