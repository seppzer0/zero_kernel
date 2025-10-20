from abc import ABC, abstractmethod


class IRomApiClient(ABC):
    """Interface for interacting with ROM projects' APIs."""

    @abstractmethod
    def map_codename(self) -> str:
        """Map the device's codename to it's devicename.

        :return: Mapped device codename for the ROM.
        :rtype: str
        """
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> str:
        """Execute the API interaction logic.

        :return: API response content.
        :rtype: str
        """
        raise NotImplementedError()
