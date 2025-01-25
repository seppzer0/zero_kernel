import os
import shutil
import requests
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from builder.tools import cleaning as cm, commands as ccmd, messages as msg
from builder.configs import DirectoryConfig as dcfg


class GithubApiClient(BaseModel):
    """Client for limited interaction with GitHub API.

    :param str project: GitHub project name (owner/repo).
    :param Optional[str]=None file_filter: A filter to select specific files from project's artifacts.
    """

    project: str
    file_filter: Optional[str] = None

    @property
    def endpoint(self) -> str:
        """Formatted endpoint.

        :return: GitHub API endpoint for specified project's latest release.
        :rtype: str
        """
        return f"https://api.github.com/repos/{self.project}/releases/latest"

    @property
    def direct_url(self) -> str:
        """Direct URL to GitHub project.

        :return: URL to GitHub project.
        :rtype: str
        """
        return f"https://github.com/{self.project}"

    def run(self) -> str | None:
        """Get the latest version of an artifact from GitHub project.

        :return: URL to download release artifact from if applicable.
        :rtype: str | None
        """
        response = requests.get(self.endpoint).json()

        # check whether the GitHub API usage is exceeded
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
                    "Found more than one suitable assets for the given parameters.\n"\
                    "      Please adjust the file filter."
                )
            else:
                data = "".join(browser_download_urls)

        except Exception:
            # if not available via API -- use regular "git clone"
            msg.note(f"Non-API GitHub resolution for {self.project}")

            rdir = Path(dcfg.assets, self.direct_url.rsplit("/", 1)[1])

            cm.remove(rdir)
            ccmd.launch(
                "git clone --depth 1 --remote-submodules --recurse-submodules --shallow-submodules {} {}"
                .format(self.direct_url, rdir)
            )
            os.chdir(rdir)
            cm.remove(".git*")
            os.chdir(dcfg.assets)
            shutil.make_archive(str(rdir), "zip", rdir)
            cm.remove(rdir)

            return None

        return data
