import os
import json
import tarfile
from pathlib import Path
from typing import Optional

from builder.tools import cleaning as cm, commands as ccmd, fileoperations as fo, messages as msg
from builder.configs import DirectoryConfig as dcfg


class ResourceManager:
    """Build resource manager."""

    _data: dict[str, dict[str, str]] = {}
    paths: dict[str, Path] = {}

    def __init__(
        self,
        codename: Optional[str] = None,
        lkv: Optional[str] = None,
        base: Optional[str] = None
    ) -> None:
        self._codename = codename
        self._lkv = lkv
        self._base = base

    def __getitem__(self, arg: Path) -> slice:
        """Custom getitem implementation for accessing data via Path-type indexes."""
        return slice(*[{True: lambda n: None, False: int}[x == ""](x) for x in (str(arg).split(":") + ["", "", ""])[:3]])

    def read_data(self) -> None:
        """Read data from all of the JSON files."""
        os.chdir(dcfg.root)
        # define paths
        tools = ""
        device = ""
        # load JSON data
        with open(dcfg.root / "builder" / "manifests" / "tools.json", encoding="utf-8") as f:
            tools = json.load(f)
        # codename and ROM are undefined only when the Docker/Podman image is being prepared
        if self._codename and self._base:
            with open(dcfg.root / "builder" / "manifests" / "devices.json", encoding="utf-8") as f:
                data = json.load(f)
                # load data only for the required codename + linux kernel version combination
                try:
                    data[self._codename][self._lkv][self._base]
                except Exception:
                    msg.error("Arguments were specified for an unsupported build, exiting..")
                device = {self._codename: data[self._codename][self._lkv][self._base]}
            # join tools and devices manifests
            self._data = {**tools, **device}
        else:
            self._data = tools
            msg.note("Only shared tools are installed.")

    def generate_paths(self) -> None:
        """Generate paths with Path objects."""
        for e in self._data:
            # convert path into it's absolute form
            self.paths[e] = dcfg.root / self._data[e]["path"]

    def download(self) -> None:
        """Download files from URLs."""
        for e in self._data:
            # break data into individual required vars
            path = Path(self._data[e]["path"])    # type: ignore
            url = self._data[e]["url"]            # type: ignore
            # break further processing into "generic" and "git" groups
            ftype = self._data[e]["type"]         # type: ignore
            match ftype:
                case "generic":
                    # download and unpack
                    # NOTE: this is specific, for .tar.gz files
                    if path.name not in os.listdir():
                        fn = url.split("/")[-1]
                        dn = fn.split(".")[0]
                        if fn not in os.listdir() and dn not in os.listdir():
                            fo.download(url)
                        msg.note(f"Unpacking {fn}..")
                        with tarfile.open(fn) as f:
                            f.extractall(path)
                        cm.remove(fn)
                        msg.done("Done!")
                    else:
                        msg.note(f"Found an existing path: {path}")
                case "git":
                    # break data into individual vars
                    branch = self._data[e]["branch"] # type: ignore
                    commit = self._data[e]["commit"] # type: ignore
                    cmd = f"git clone -b {branch} --depth 1 --remote-submodules --recurse-submodules --shallow-submodules {url} {path}"
                    # full commit history is required in two instances:
                    # - for KernelSU -- to define it's version based on *full* commit history;
                    # - for commit checkout -- to checkout a specific commit in the history.
                    if e.lower() == "kernelsu" or commit:
                        cmd = cmd.replace(" --depth 1", "")
                    if not path.is_dir():
                        ccmd.launch(cmd)
                        # checkout a specific commit if it is specified
                        if commit:
                            cmd = f"git checkout {commit}"
                            os.chdir(path)
                            ccmd.launch(cmd)
                            os.chdir(dcfg.root)
                    else:
                        msg.note(f"Found an existing path: {path}")
                case _:
                    msg.error("Invalid resource type detected. Use only: generic, git.")

    def export_path(self) -> None:
        """Add path to PATH."""
        for elem in self.paths:
            p = self.paths[elem]
            pathenv = str(f"{p}/bin/")
            os.environ["PATH"] = pathenv + os.pathsep + os.getenv("PATH") # type: ignore
