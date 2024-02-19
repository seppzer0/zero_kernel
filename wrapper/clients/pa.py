from wrapper.clients.rom_api import RomApi


class ParanoidAndroidApi(RomApi):
    """Limited interaction with ParanoidAndroid API."""

    endpoint: str = "https://api.paranoidandroid.co/updates/{}"
    json_key: str = "updates"
    rom_name: str = "PA"
