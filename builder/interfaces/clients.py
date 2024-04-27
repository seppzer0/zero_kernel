from abc import ABC, abstractmethod


class IRomApi(ABC):
    """Interface for interacting with ROM projects' APIs."""

    @abstractmethod
    def codename_mapper(self) -> str:
        """Codename-to-devicename mapper."""
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> str:
        """Execute the API interaction logic."""
        raise NotImplementedError()
