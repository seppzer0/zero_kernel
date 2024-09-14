from builder.clients.rom_api import RomApiClient


class LineageOsApiClient(RomApiClient):
    """Client for limited interaction with Lineage API."""

    endpoint: str = "https://download.lineageos.org/api/v1/{}/nightly/ro.build.version.incremental"
    json_key: str = "response"
    rom_name: str = "LOS"
