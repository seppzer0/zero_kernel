from pathlib import Path


apath = Path(Path(__file__).absolute().parents[1])
with open(Path(apath, "pyproject.toml")) as f:
    print(f.read().split('version = "')[1].split('"')[0])
