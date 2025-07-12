import logging
from pydantic import BaseModel

from builder.core import KernelBuilder
from builder.tools import banner, fileoperations as fo
from builder.interfaces import ICommand


log = logging.getLogger("ZeroKernelLogger")


class KernelCommand(BaseModel, ICommand):
    """Command responsible for launching the 'kernel_builder' core module directly.

    :param builder.core.KernelBuilder kernel_builder: Kernel builder object.
    """

    kernel_builder: KernelBuilder

    def execute(self) -> None:
        self.kernel_builder.run()
