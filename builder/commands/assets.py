from typing import Literal
from pydantic import BaseModel

from builder.core import AssetsCollector
from builder.interfaces import ICommand


class AssetsCommand(BaseModel, ICommand):
    """Command responsible for launching the 'assets_collector' core module directly.

    :param str codename: Device codename.
    :param str base: Kernel source base.
    :param Literal["full","minimal"] chroot: Chroot type.
    :param bool rom_only: Flag indicating ROM-only asset collection.
    :param bool ksu: Flag indicating KernelSU support.
    """

    codename: str
    base: str
    chroot: Literal["full", "minimal"]
    clean_assets: bool
    rom_only: bool
    ksu: bool

    def execute(self) -> None:
        ac = AssetsCollector(**self.__dict__)
        ac.run()
