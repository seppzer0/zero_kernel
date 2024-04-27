from pydantic import BaseModel

from builder.core import KernelBuilder
from builder.interfaces import ICommand

class KernelCommand(BaseModel, ICommand):
    """Command responsible for launching the 'kernel_builder' core module directly.

    :param str codename: Device codename.
    :param str base: Kernel source base.
    :param str lkv: Linux kernel version.
    :param bool clean_kernel: Flag to clean folder with kernel sources.
    :param bool ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    lkv: str
    clean_kernel: bool
    ksu: bool

    def execute(self) -> None:
        kb = KernelBuilder(**self.__dict__)
        kb.run()
