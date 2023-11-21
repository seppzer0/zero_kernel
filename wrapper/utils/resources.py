import os
import json
import tarfile
from pathlib import Path
from typing import Optional

import tools.cleaning as cm
import tools.messages as msg
import tools.commands as ccmd
import tools.fileoperations as fo

from configs import Config as cfg


class Resources:
    """An entity for managing build resources."""

    _root: Path = cfg.DIR_ROOT
    paths: list[str] = []

    def __init__(
            self,
            codename: Optional[str] = "",
            lversion: Optional[str] = "",
            rom: Optional[str] = ""
        ) -> None:
        self._codename = codename
        self._lversion = lversion
        self._rom = rom

    def path_gen(self) -> dict[str]:
        """Generate paths from JSON data."""
        os.chdir(self._root)
        # define paths
        tools = ""
        device = ""
        # load JSON data
        with open(self._root / "wrapper" / "manifests" / "tools.json") as f:
            tools = json.load(f)
        # codename and ROM are undefined only when the Docker/Podman image is being prepared
        if self._codename and self._rom:
            with open(self._root / "wrapper" / "manifests" / "devices.json") as f:
                data = json.load(f)
                # load data only for the required codename + linux kernel version combination
                device = {self._codename: data[self._codename][self._lversion][self._rom]}
            # join tools and devices manifests
            self.paths = {**tools, **device}
        else:
            self.paths = tools
            msg.note("Only shared tools are installed.")
        for e in self.paths:
            # convert path into it's absolute form
            self.paths[e]["path"] = self._root / self.paths[e]["path"]

    def download(self) -> None:
        """Download files from URLs."""
        for e in self.paths:
            # break data into individual required vars
            path = self.paths[e]["path"]
            url = self.paths[e]["url"]
            # break further processing into "generic" and "git" groups
            ftype = self.paths[e]["type"]
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
                    branch = self.paths[e]["branch"]
                    commit = self.paths[e]["commit"]
                    cmd = f"git clone -b {branch} --depth 1 {url} {path}"
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
                            os.chdir(self._root)
                    else:
                        msg.note(f"Found an existing path: {path}")
                case _:
                    msg.error("Invalid resource type detected. Use only: generic, git.")
    
    def export_path(self) -> None:
        """Add path to PATH.

        :param path: A path that is being exported to PATH.
        """
        for elem in self.paths:
            p = self.paths[elem]["path"]
            pathenv = str(f"{p}/bin/")
            os.environ["PATH"] = pathenv + os.pathsep + os.getenv("PATH")
