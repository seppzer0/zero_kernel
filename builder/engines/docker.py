import os
from typing import override

from builder.tools import commands as ccmd, messages as msg
from builder.interfaces import IDockerEngine

from builder.engines.container_engine import ContainerEngine


class DockerEngine(ContainerEngine, IDockerEngine):
    """Docker engine."""

    @staticmethod
    def _force_buildkit() -> None:
        os.environ["DOCKER_BUILDKIT"] = "1"

    def _check_cache(self) -> bool:
        img_cache_cmd = f'{self.benv} images --format {"{{.Repository}}"}'
        img_cache = ccmd.launch(img_cache_cmd, get_output=True)
        check = True if self.name_image in img_cache else False
        return check

    @override
    def __enter__(self) -> None:
        self._force_buildkit()
        # build image only if it is not present in local cache
        if not self._check_cache():
            self.build_image()
        else:
            msg.note("\nDocker image already in local cache, skipping it's build..\n")
        self.create_dirs()
