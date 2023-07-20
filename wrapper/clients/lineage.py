import requests

import wrapper.tools.messages as msg


class LineageApi:
    """Interaction with Lineage API."""

    def __init__(self, device: str, rom_only: bool) -> None:
        self._device = device
        self._rom_only = rom_only

    def run(self) -> str:
        """Get the latest version of LineageOS ROM."""
        romtype = "nightly"
        incr = "ro.build.version.incremental"
        url = f"https://download.lineageos.org/api/v1/{self._device}/{romtype}/{incr}"
        data = requests.get(url)
        try:
            data = data.json()["response"][0]["url"]
        except Exception:
            exit_flag = False if self._rom_only else True
            msg.error(f"Could not connect to LOS API, HTTP status code: {data.status_code}",
                      dont_exit=exit_flag)
        return data
