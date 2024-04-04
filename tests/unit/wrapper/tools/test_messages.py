import pytest

from builder.tools import messages as msg


def test__message_note__validate(capfd):
    """Check "note" message construction."""
    m = "This is a test message."
    expected_result = f"[ * ] {m}"
    msg.note(m)
    out, err = capfd.readouterr()
    assert out.rstrip() == expected_result


@pytest.mark.parametrize("dont_exit", (False, True))
def test__message_error__validate(capfd, dont_exit: bool) -> None:
    """Check "error" message construction."""
    m = "This is a test message."
    expected_result = f"[ ! ] {m}"
    if dont_exit is False:
        with pytest.raises(SystemExit):
            msg.error(m, dont_exit)
    else:
        msg.error(m, dont_exit)
        out, err = capfd.readouterr()
        assert err.rstrip() == expected_result


def test__message_done__validate(capfd) -> None:
    """Check "done" message construction."""
    m = "This is a test message."
    expected_result = f"[ + ] {m}"
    msg.done(m)
    out, err = capfd.readouterr()
    assert out.rstrip() == expected_result


def test__message_cancel__validate(capfd) -> None:
    """Check "cancel" message construction."""
    m = "This is a test message."
    expected_result = f"[ ~ ] {m}"
    # system exit with code 0 is still a SystemExit
    with pytest.raises(SystemExit):
        msg.cancel(m)
    out, err = capfd.readouterr()
    assert out.rstrip() == expected_result


def test__message_debug__validate(capfd) -> None:
    """Check "debug" message construction."""
    m = "This is a test message."
    expected_result = f"[ DEBUG ] {m}"
    msg.debug(m)
    out, err = capfd.readouterr()
    assert out.rstrip() == expected_result
