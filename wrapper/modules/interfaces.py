from abc import ABC, abstractmethod

class IModuleExecutor(ABC):
    """A simple interface for module's logic execution."""
    
    @abstractmethod
    def run(self) -> None:
         """Execute the module logic."""
         raise NotImplementedError()
