from .template_rom_api import TemplateRomApi


class LineageOsApi(TemplateRomApi):
    """Limited interaction with Lineage API."""

    endpoint: str = "https://download.lineageos.org/api/v1/{}/nightly/ro.build.version.incremental"
    json_key: str = "response"
    rom_name: str = "LOS"

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.endpoint = self.endpoint.format(self.codename)
