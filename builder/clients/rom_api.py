import requests
from pydantic import BaseModel

from builder.tools import messages as msg
from builder.interfaces import IRomApiClient


class RomApiClient(BaseModel, IRomApiClient):
    """Generic class for interacting with ROMs' APIs.

    :param str endpoint: API endpoint to interact with.
    :param str json_key: A JSON key to look for in the response data.
    :param str rom_name: ROM project's name.
    :param bool rom_only: Flag indicating ROM-only asset collection.
    """

    endpoint: str
    json_key: str
    rom_name: str
    codename: str
    rom_only: bool

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.endpoint = self.endpoint.format(self.codename_mapper())

    def codename_mapper(self) -> str:
        # by default, codename is devicename
        return self.codename

    def run(self) -> str:
        data = requests.get(self.endpoint)
        try:
            data = data.json()[self.json_key][0]["url"]
        except Exception:
            exit_flag = False if self.rom_only else True
            msg.error(
                f"Could not connect to {self.rom_name} API, HTTP status code: {data.status_code}",
                dont_exit=exit_flag
            )
        return str(data)
