import os
import shutil
import requests
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

import wrapper.tools.cleaning as cm
import wrapper.tools.messages as msg
import wrapper.tools.commands as ccmd

from wrapper.configs.directory_config import DirectoryConfig as dcfg


class GitHubApi(BaseModel):
    """Limited interaction with GitHub API.

    :param _endpoint: API endpoint to interact with.
    :param _direct_url: Direct URL for the specified repo.
    :param project: GitHub project name (owner/repo).
    :param file_filter: A filter to select specific files from project's artifacts.
    """

    _endpoint = "https://api.github.com/repos/{}/releases/latest"
    _direct_url = "https://github.com/{}"

    project: str
    file_filter: Optional[str] = None

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._endpoint = self._endpoint.format(self.project)
        self._direct_url = self._direct_url.format(self.project)

    def run(self) -> str:
        """Get the latest version of an artifact from GitHub project."""
        response = requests.get(self._endpoint).json()
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
        try:
            # get direct download URL and optionally filter it with the given parameter
            data = response["assets"]
            browser_download_urls = []
            for elem in data:
                url_dto = elem["browser_download_url"]
                if url_dto and self.file_filter in url_dto:
                    browser_download_urls.append(url_dto)
            # if there is more than one fitting response -- throw an error
            if len(browser_download_urls) > 1:
                msg.error(
                    "Found more than one suitable assets for the given paramenters.\n"\
                    "      Please adjust the file filter."
                )
            else:
                data = "".join(browser_download_urls)
        except Exception:
            # if not available via API -- use regular "git clone"
            rdir = Path(dcfg.assets, self._direct_url.rsplit("/", 1)[1])
            msg.note(f"Non-API GitHub resolution for {self.project}")
            cm.remove(rdir)
            ccmd.launch(f"git clone --depth 1 --remote-submodules --recurse-submodules --shallow-submodules {self._direct_url} {rdir}")
            os.chdir(rdir)
            cm.remove(".git*")
            os.chdir(dcfg.assets)
            shutil.make_archive(str(rdir), "zip", rdir)
            cm.remove(rdir)
            return
            data = None
        return data
