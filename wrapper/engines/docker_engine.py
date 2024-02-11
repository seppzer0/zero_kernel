import os
from typing import override

import tools.messages as msg
import tools.commands as ccmd

from .template_container_engine import TemplateContainerEngine


class DockerEngine(TemplateContainerEngine):
    """Docker engine."""

    benv: str = "docker"

    def __init__(self, config: dict) -> None:
        super().__init__(config)

    @staticmethod
    def _force_buildkit() -> None:
        """Force enable Docker BuildKit."""
        os.environ["DOCKER_BUILDKIT"] = "1"

    def _check_cache(self) -> bool:
        """Check local Docker cache for the specified image."""
        img_cache_cmd = f'{self.benv} images --format {"{{.Repository}}"}'
        img_cache = ccmd.launch(img_cache_cmd, get_output=True)
        check = True if self.name_image in img_cache else False
        return check

    @override
    def run(self) -> None:
        self._force_buildkit()
        # build image only if it is not present in local cache
        if not self._check_cache():
            self.build()
        else:
            msg.note("\nDocker image already in local cache, skipping it's build..\n")
        # form the final command to create container
        cmd = '{} run {} {} /bin/bash -c "{}"'.format(
            self.benv,
            " ".join(self.container_options),
            self.name_image,
            self.wrapper_cmd
        )
        # prepare directories
        self.create_dirs()
        ccmd.launch(cmd)
        # navigate to root directory and clean image from host machine
        os.chdir(self.dir_init)
        if self.clean_image:
            ccmd.launch(f"{self.benv} rmi {self.name_image}")
