from abc import ABC, abstractmethod


class ICommand(ABC):
    """Interface for builder's commands."""

    @abstractmethod
    def execute(self) -> None:
        """Execute command's logic.

        :return: None
        """
        raise NotImplementedError()
