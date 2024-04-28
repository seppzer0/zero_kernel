from typing import override

from builder.clients.rom_api import RomApiClient


class ParanoidAndroidApiClient(RomApiClient):
    """Limited interaction with ParanoidAndroid API."""

    endpoint: str = "https://api.paranoidandroid.co/updates/{}"
    json_key: str = "updates"
    rom_name: str = "PA"

    @override
    def codename_mapper(self) -> str:
        # specific rules for PA's API
        specials = {
            "dumpling": "oneplus5t",
            "cheeseburger": "oneplus5",
        }
        return specials[self.codename] if self.codename in specials else self.codename
