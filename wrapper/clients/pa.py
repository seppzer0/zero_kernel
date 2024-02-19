from typing import override

from wrapper.clients.rom_api import RomApi


class ParanoidAndroidApi(RomApi):
    """Limited interaction with ParanoidAndroid API."""

    endpoint: str = "https://api.paranoidandroid.co/updates/{}"
    json_key: str = "updates"
    rom_name: str = "PA"

    @override
    @property
    def codename_mapper(self) -> str:
        # specific rules for PA's API
        specials = {
            "dumpling": "oneplus5t",
            "cheeseburger": "oneplus5",
        }
        return specials[self.codename] if self.codename in specials else self.codename
