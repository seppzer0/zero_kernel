from typing import Any
from requests import Response
from abc import ABC, abstractmethod


class IRomApi(ABC):
    """An interface for interacting with ROM projects' APIs."""

    @abstractmethod
    def codename_mapper(self) -> str:
        """Codename-to-devicename mapper."""
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> Any | Response:
        """Execute the API interaction logic."""
        raise NotImplementedError()
