import os
import platform
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

ROOTPATH: Path = Path(__file__).absolute().parents[1]
INTEPRETER: str = "python" if platform.system() == "Windows" else "python3"


class Tester:
    """A single class for all types of tests."""

    @staticmethod
    def _launch_cmd(cmd: str) -> CompletedProcess:
        """Launch specified command with STDERR."""
        return subprocess.run(cmd, shell=True, check=True)

    def pyright_checks(self) -> None:
        """Run typing checks with Pyright."""
        print("\n=== Pyright checks: Start ===")
        self._launch_cmd(f"{INTEPRETER} -m pyright")
        print("=== Pyright checks: Finish ===")

    def pytest_checks(self) -> bool:
        """Run unit tests with Pytest and coverage checks."""
        os.environ["PYTHONPATH"] = str(ROOTPATH)
        print("\n=== Pytest checks: Start ===")
        self._launch_cmd(f"{INTEPRETER} -m pytest -vv tests/ --cov")
        print("=== Pytest checks: Finish ===")

    def bandit_checks(self) -> None:
        """Run SAST with Bandit."""
        fmts = ("json", "html")
        cps = []
        for fmt in fmts:
            cps.append(self._launch_cmd(f"python3 -m bandit -r -f {fmt} {ROOTPATH} -o report.{fmt}"))
        return cps


def main() -> None:
    os.chdir(ROOTPATH)
    t = Tester()
    t.pyright_checks()
    t.pytest_checks()
    #t.bandit_checks()


if __name__ == "__main__":
    main()
