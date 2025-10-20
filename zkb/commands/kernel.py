import logging
from pydantic import BaseModel

from zkb.core import KernelBuilder
from zkb.tools import banner, fileoperations as fo
from zkb.interfaces import ICommand


log = logging.getLogger("ZeroKernelLogger")


class KernelCommand(BaseModel, ICommand):
    """Command responsible for launching the 'kernel_builder' core module directly.

    :param builder.core.KernelBuilder kernel_builder: Kernel builder object.
    """

    kernel_builder: KernelBuilder

    def execute(self) -> None:
        self.kernel_builder.run()
