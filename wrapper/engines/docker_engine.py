import os
from typing import override

import tools.messages as msg
import tools.commands as ccmd

from .container_engine import ContainerEngine


class DockerEngine(ContainerEngine):
    """Docker engine."""

    @staticmethod
    def _force_buildkit() -> None:
        """Force enable Docker BuildKit."""
        os.environ["DOCKER_BUILDKIT"] = "1"

    def _check_cache(self) -> bool:
        """Check local Docker cache for the specified image.

        For now, this is done for Docker exclusively.
        """
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
        os.chdir(self.wdir_local)
        if self.clean_image:
            ccmd.launch(f"{self.benv} rmi {self.name_image}")
