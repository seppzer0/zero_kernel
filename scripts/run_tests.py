import os
import subprocess
from pathlib import Path

ROOTPATH: Path = Path(Path(__file__).absolute().parents[1])


class Tester:
    """A single class for all types of tests."""

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

    def bandit_checks(self) -> None:
        """Run SAST with Bandit."""
        fmts = ("json", "html")
        for fmt in fmts:
            self._launch(f"python3 -m bandit -r -f {fmt} {ROOTPATH} -o report.{fmt}")


def main() -> None:
    os.chdir(ROOTPATH)
    t = Tester()
    t.pytest_checks()
    t.pyright_checks()
    t.bandit_checks()


if __name__ == "__main__":
    main()
