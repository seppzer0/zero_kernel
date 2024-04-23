"""
Script to generate class diagrams of all modules im plantuml (.puml) format.
"""

import os
import subprocess
from pathlib import Path

ROOTPATH: Path = Path(__file__).absolute().parents[1]
DOCSPATH: Path = ROOTPATH / "docs" / "architecture"
APPPATH: Path = ROOTPATH / "devciai"


def run_cmd(cmd: str) -> subprocess.CompletedProcess:
    """Launch the specified command in specific wrapping."""
    return subprocess.run(cmd, shell=True, check=True)


def check_docs_dir() -> None:
    """Check the state of docs directory with architecture documentation."""
    try:
        os.listdir(DOCSPATH)
    except Exception:
        os.makedirs(DOCSPATH, exist_ok=True)


def generate_docs() -> None:
    """Generate .puml files."""
    for elem in os.listdir(APPPATH):
        full_path = APPPATH / elem
        if full_path.is_dir() and "__init__.py" in os.listdir(full_path):
            package_docs_path = DOCSPATH / elem
            os.makedirs(package_docs_path, exist_ok=True)
            run_cmd(f"pyreverse {APPPATH / elem} -o puml -d {package_docs_path}")


def main() -> None:
    check_docs_dir()
    generate_docs()


if __name__ == "__main__":
    main()
