from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    """A variable storage to use across the application."""
    DIR_ROOT: Path = Path(__file__).absolute().parents[2]
    DIR_KERNEL: str = "kernel"
    DIR_ASSETS: str = "assets"
    DIR_BUNDLE: str = "bundle"
