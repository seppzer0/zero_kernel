from pathlib import Path
from pydantic.dataclasses import dataclass

@dataclass
class DirectoryConfig:
    """A config for key directory paths."""
    root: Path = Path(__file__).absolute().parents[2]
    kernel: Path = Path(root, "kernel")
    assets: Path = Path(root, "assets")
    bundle: Path = Path(root, "bundle")
