from abc import ABC, abstractmethod


class IResourceManager(ABC):
    """Interface for the resource manager."""

    @abstractmethod
    def read_data(self) -> None:
        """Read data from all of the JSON files."""
        raise NotImplementedError()

    @abstractmethod
    def generate_paths(self) -> None:
        """Generate paths with Path objects."""
        raise NotImplementedError()
    
    @abstractmethod
    def download(self) -> None:
        """Download files from URLs."""
        raise NotImplementedError()
    
    @abstractmethod
    def export_path(self) -> None:
        """Export path to PATH."""
        raise NotImplementedError()
