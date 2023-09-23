import requests

import tools.messages as msg


class ParanoidAndroidApi:
    """Limited interaction with ParanoidAndroid API."""

    _endpoint = "https://api.paranoidandroid.co/updates/{}"

    def __init__(self, codename: str, rom_only: bool) -> None:
        self._codename = codename
        self._rom_only = rom_only
        self._endpoint = self._endpoint.format(self._codename_pa)

    @property
    def _codename_pa(self) -> str:
        """Custom codename-to-device mapper for PA API specifically."""
        name_dict = {
            "dumpling": "oneplus5t",
            "cheeseburger": "oneplus5",
        }
        return name_dict[self._codename]

    def run(self) -> str:
        """Get the latest version of ParanoidAndroid ROM."""
        data = requests.get(self._endpoint)
        try:
            data = data.json()["updates"][0]["url"]
        except Exception:
            exit_flag = False if self._rom_only else True
            msg.error(
                f"Could not connect to PA API, HTTP status code: {data.status_code}",
                dont_exit=exit_flag
            )
        return data
