import logging
from typing import Literal
from pydantic import BaseModel

from builder.core import AssetsCollector
from builder.tools import banner, fileoperations as fo
from builder.interfaces import ICommand


log = logging.getLogger("ZeroKernelLogger")


class AssetsCommand(BaseModel, ICommand):
    """Command responsible for launching the 'assets_collector' core module directly.

    :param builder.core.AssetsCollector assets_collector: Assets collector object.
    """

    assets_collector: AssetsCollector

    def execute(self) -> None:
        self.assets_collector.run()
