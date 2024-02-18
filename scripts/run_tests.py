import os
import subprocess
from typing import List
from pathlib import Path
from subprocess import CompletedProcess

ROOTPATH: Path = Path(Path(__file__).absolute().parents[1])


class Tester:
    """A single class for all types of tests."""

    def _launch_cmd(cmd: str) -> CompletedProcess:
        """Launch specified command."""
        return subprocess.run(cmd, shell=True, check=True)

    def pytest_checks(self) -> CompletedProcess:
        """Run unit tests with Pytest and coverage checks."""
        os.environ["PYTHONPATH"] = ROOTPATH
        return self._launch_cmd("python3 -m pytest tests/ --cov")

    def pyright_checks(self) -> CompletedProcess:
        """Run type (hint) checks with Pyright."""
        return self._launch_cmd("python3 -m pyright wrapper")

    def bandit_checks(self) -> List[CompletedProcess]:
        """Run SAST with Bandit."""
        fmts = ("json", "html")
        cps = []
        for fmt in fmts:
            cps.append(self._launch(f"python3 -m bandit -r -f {fmt} {ROOTPATH} -o report.{fmt}"))
        return cps


def main() -> None:
    os.chdir(ROOTPATH)
    t = Tester()
    t.pytest_checks()
    t.pyright_checks()
    t.bandit_checks()


if __name__ == "__main__":
    main()
