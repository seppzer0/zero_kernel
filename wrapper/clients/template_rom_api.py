import requests

import tools.messages as msg


class TemplateRomApi:
    """A template class for interacting with ROMs' APIs."""

    endpoint: str
    json_key: str
    rom_name: str

    def __init__(self, codename: str, rom_only: str) -> None:
        self.codename = codename
        self.rom_only = rom_only

    def run(self) -> str:
        """Get the latest build of the ROM."""
        data = requests.get(self.endpoint)
        try:
            data = data.json()[self.json_key][0]["url"]
        except Exception:
            exit_flag = False if self.rom_only else True
            msg.error(
                f"Could not connect to {self.rom_name} API, HTTP status code: {data.status_code}",
                dont_exit=exit_flag
            )
        return data
