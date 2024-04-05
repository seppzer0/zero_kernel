from pathlib import Path


def main() -> None:
    rootpath = Path(__file__).absolute().parents[1]
    with open(rootpath / "pyproject.toml", encoding="utf-8") as f:
        print(f.read().split('version = "')[1].split('"')[0])


if __name__ == "__main__":
    main()
