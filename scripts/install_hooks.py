import os
import sys
import logging
import textwrap
from pathlib import Path


logging.basicConfig(
    format="[%(asctime)s] [%(levelname).1s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)


class HookInstaller:
    """Manager of git hooks for the repository."""

    def __init__(self) -> None:
        self.__path = Path(__file__).absolute().parents[1] / ".git" / "hooks" / "pre-commit"

    @property
    def hook(self) -> str:
        """Contents of hook to be installed.

        :return: Contents of a git hook.
        :rtype: str
        """
        hook = textwrap.dedent(
            """
            #!/usr/bin/env bash

            ARGS=(hook-impl --config=.pre-commit-config.yaml --hook-type=pre-commit)
            HERE="$(cd "$(dirname "$0")" && pwd)"
            ARGS+=(--hook-dir "$HERE" -- "$@")

            exec uv run -m pre_commit "${ARGS[@]}"
            """
        )
        # strip only leading whitespace
        return hook.lstrip()

    def install(self) -> None:
        """Write the hook to the specified file.

        :return: None
        """
        with open(self.__path, "w") as f:
            f.write(self.hook)
        os.chmod(self.__path, 0o755)


def main() -> None:
    logging.info("Installing git hooks...")
    hi = HookInstaller()
    hi.install()
    logging.info("Done! Hooks installed successfully.")


if __name__ == "__main__":
    main()
