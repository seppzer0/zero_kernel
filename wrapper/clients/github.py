import os
import shutil
import requests
from pathlib import Path

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg
import wrapper.tools.commands as ccmd


class GitHubApi:
    """Limited interaction with GitHub API."""

    def __init__(self, project: str, assetdir: str) -> None:
        self._project = project
        self._assetdir = assetdir

    def run(self) -> str:
        """Get the latest version of an artifact from GitHub project."""
        url = f"https://github.com/{self._project}"
        api_url = f"https://api.github.com/repos/{self._project}/releases/latest"
        response = requests.get(api_url).json()
        # this will check whether the GitHub API usage is exceeded
        try:
            data = response["message"]
            if "API rate limit" in data:
                msg.error(
                    "GitHub API call rate was exceeded, try a bit later.",
                    dont_exit=True
                )
        except Exception:
            pass
        # get the latest version of GitHub project via API
        try:
            data = response["assets"][0]["browser_download_url"]
        except Exception:
            # if not available via API -- use "git clone"
            rdir = Path(self._assetdir, url.rsplit("/", 1)[1])
            msg.note(f"Non-API GitHub resolution for {self._project}")
            cm.remove(rdir)
            ccmd.launch(f"git clone --depth 1 {url} {rdir}")
            os.chdir(rdir)
            cm.remove(".git*")
            os.chdir(self._assetdir)
            shutil.make_archive(f"{rdir}", "zip", rdir)
            cm.remove(rdir)
            return
        return data
