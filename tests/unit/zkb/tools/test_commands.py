import pytest

from zkb.tools import commands as ccmd


def test__launch__invalid_command(capfd) -> None:
    """Test an invalid command execution handling."""
    cmd = "some_invalid_command"
    with pytest.raises(SystemExit):
        ccmd.launch(cmd)
