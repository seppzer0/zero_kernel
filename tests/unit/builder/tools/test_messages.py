import pytest
import logging


log = logging.getLogger("ZeroKernelLogger")


#def test__message_info__validate(capfd) -> None:
#    """Check "info" message construction."""
#    m = "This is a test message."
#    expected_result = f"[I] {m}"
#    log.error(m)
#    out, err = capfd.readouterr()
#    assert expected_result in out.rstrip()
#
#
#def test__message_error__validate(capfd) -> None:
#    """Check "error" message construction."""
#    m = "This is a test message."
#    expected_result = f"[E] {m}"
#    log.error(m)
#    out, err = capfd.readouterr()
#    assert expected_result in out.rstrip()
#
#
#def test__message_warning__validate(capfd) -> None:
#    """Check "warning" message construction."""
#    m = "This is a test message."
#    expected_result = f"[W] {m}"
#    # system exit with code 0 is still a SystemExit
#    with pytest.raises(SystemExit):
#        log.warning(m)
#    out, err = capfd.readouterr()
#    assert expected_result in out.rstrip()
#
#
#def test__message_debug__validate(capfd) -> None:
#    """Check "debug" message construction."""
#    m = "This is a test message."
#    expected_result = f"[D] {m}"
#    log.debug(m)
#    out, err = capfd.readouterr()
#    assert out.rstrip() == expected_result
