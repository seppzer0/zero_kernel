"""
Script to generate class diagrams of all packages in plantuml (.puml) format.
"""

import os
import shutil
import subprocess
from pathlib import Path

ROOTPATH: Path = Path(__file__).absolute().parents[1]
DOCSPATH: Path = ROOTPATH / "docs" / "architecture"
APPPATH: Path = ROOTPATH / "builder"


def run_cmd(cmd: str) -> subprocess.CompletedProcess:
    """Launch the specified command in specific wrapping."""
    return subprocess.run(cmd, shell=True, check=True)


def clean_dir() -> None:
    """Create a clean docs directory."""
    shutil.rmtree(DOCSPATH, ignore_errors=True)
    os.makedirs(DOCSPATH)


def generate_docs() -> None:
    """Generate .puml files."""
    for elem in os.listdir(APPPATH):
        full_path = APPPATH / elem
        if full_path.is_dir() and "__init__.py" in os.listdir(full_path):
            package_docs_path = DOCSPATH / elem
            os.makedirs(package_docs_path, exist_ok=True)
            run_cmd(f"pyreverse {APPPATH / elem} -o puml -d {package_docs_path}")
            # edit "class" into "interface" for interfaces
            if elem == "interfaces":
                data = ""
                with open(package_docs_path / "classes.puml", "r") as f:
                    data = f.read()
                data = data.replace("class ", "interface ")
                with open(package_docs_path / "classes.puml", "w") as f:
                    f.write(data)


def main() -> None:
    clean_dir()
    generate_docs()


if __name__ == "__main__":
    main()
