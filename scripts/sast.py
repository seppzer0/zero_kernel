from pathlib import Path

import tools.commands as ccmd


# generate reports in multiple file formats
formats = ("json", "html")
apath = Path(Path(__file__).absolute().parents[1], "wrapper")
for ft in formats:
    ccmd.launch(f"python3 -m bandit -r -f {ft} {apath} -o report.{ft}", loglvl="verbose")
