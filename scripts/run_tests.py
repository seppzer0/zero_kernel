import os
import subprocess
from pathlib import Path


class Tester:
    """A single class for all types of tests."""

    rootpath: Path = Path(Path(__file__).absolute().parents[1])

    def _launch_cmd(cmd: str) -> None:
        """Launch specified command."""
        subprocess.run(cmd, shell=True, check=True)

    def pytest_checks(self) -> None:
        """Run Unit tests with Pytest.

        Includes coverage checks.
        """
        os.environ["PYTHONPATH"] = self.rootpath
        self._launch_cmd("pytest tests --cov")

    def pyright_checks(self) -> None:
        """Run type (hint) checks with Pyright."""
        self._launch_cmd("pyright wrapper")


def main() -> None:
    rootpath = Path(Path(__file__).absolute().parents[1])
    os.chdir(rootpath)
    t = Tester()
    t.pytest_checks()
    t.pyright_checks()


if __name__ == "__main__":
    main()
