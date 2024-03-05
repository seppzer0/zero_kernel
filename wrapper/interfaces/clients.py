from abc import ABC, abstractmethod


class IRomApi(ABC):
    """An interface for interacting with ROM projects' APIs."""

    @property
    @abstractmethod
    def codename_mapper(self) -> str:
        """Codename-to-devicename mapper."""
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        """Execute the API interaction logic."""
        raise NotImplementedError()
