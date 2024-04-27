from pathlib import Path
from pydantic.dataclasses import dataclass


@dataclass
class DirectoryConfig:
    """Config for key directory paths."""
    root: Path = Path(__file__).absolute().parents[2]
    kernel: Path = root / "kernel"
    assets: Path = root / "assets"
    bundle: Path = root / "bundle"
