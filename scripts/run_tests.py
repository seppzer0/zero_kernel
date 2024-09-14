import os
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

ROOTPATH: Path = Path(__file__).absolute().parents[1]


class Tester:
    """Single class for all types of tests."""

    @staticmethod
    def _launch_cmd(cmd: str) -> CompletedProcess:
        """Launch specified command."""
        return subprocess.run(cmd, shell=True, check=True)

    def pyright_check(self) -> None:
        """Run typing checks with Pyright."""
        print("\n=== Pyright checks: Start ===")
        self._launch_cmd("uv run python -m pyright")
        print("=== Pyright checks: Finish ===")

    def pytest_check(self) -> None:
        """Run unit tests with Pytest and coverage checks."""
        os.environ["PYTHONPATH"] = str(ROOTPATH)
        print("\n=== Pytest checks: Start ===")
        self._launch_cmd("uv run python -m pytest -vv tests/ --cov")
        print("=== Pytest checks: Finish ===")

    def bandit_check(self) -> None:
        """Run SAST with Bandit."""
        fmts = ("json", "html")
        for fmt in fmts:
            self._launch_cmd(f"uv run python -m bandit -r -f {fmt} {ROOTPATH} -o report.{fmt}")


def main() -> None:
    os.chdir(ROOTPATH)
    t = Tester()
    t.pyright_check()
    t.pytest_check()
    #t.bandit_check()


if __name__ == "__main__":
    main()
