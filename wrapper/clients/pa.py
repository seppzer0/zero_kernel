from .template_rom_api import TemplateRomApi


class ParanoidAndroidApi(TemplateRomApi):
    """Limited interaction with ParanoidAndroid API."""

    endpoint: str = "https://api.paranoidandroid.co/updates/{}"
    json_key: str = "updates"
    rom_name: str = "PA"

    def __init__(self, **data) -> None:
        super().__init__(**data)
        # PA has a custom codename/device naming
        self.endpoint = self.endpoint.format(self._codename_pa)

    @property
    def _codename_pa(self) -> str:
        """Custom codename-to-device mapper for PA API."""
        custom_names = {
            "dumpling": "oneplus5t",
            "cheeseburger": "oneplus5",
        }
        res = self.codename if self.codename not in custom_names else custom_names[self.codename]
        return res
