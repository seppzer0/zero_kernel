import requests

import tools.messages as msg


class LineageOsApi:
    """Limited interaction with Lineage API."""

    _endpoint = "https://download.lineageos.org/api/v1/{}/{}/{}"

    def __init__(self, codename: str, rom_only: bool) -> None:
        self._codename = codename
        self._rom_only = rom_only
        self._endpoint = self._endpoint.format(codename, "nightly", "ro.build.version.incremental")

    def run(self) -> str:
        """Get the latest version of LineageOS ROM."""
        data = requests.get(self._endpoint)
        try:
            data = data.json()["response"][0]["url"]
        except Exception:
            exit_flag = False if self._rom_only else True
            msg.error(f"Could not connect to LOS API, HTTP status code: {data.status_code}",
                      dont_exit=exit_flag)
        return data
