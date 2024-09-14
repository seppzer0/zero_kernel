import sys


def banner(text: str) -> None:
    """Print out banner.

    :param str text: Text to wrap.
    """
    banner_len = len(text) + 6
    print("\n" + "*" * banner_len)
    print(f"** {text} **")
    print("** by seppzer0" + " " * (banner_len - 17) + " **")
    print("*" * banner_len)
    print("\n", end="")


def note(text: str) -> None:
    """Wrap a "note" message.

    :param str text: Text to wrap.
    """
    print(f"[ * ] {text}")


def error(text: str, dont_exit: bool = False) -> None:
    """Wrap an "error" message.

    Includes system exit with an error code.

    :param str text: Text to wrap.
    """
    print(f"[ ! ] {text}", file=sys.stderr)
    if not dont_exit:
        sys.exit(1)


def cancel(text: str) -> None:
    """Wrap a "cancel" message.

    :param str text: Text to wrap.
    """
    print(f"[ ~ ] {text}")
    sys.exit(0)


def done(text: str) -> None:
    """Wrap a "done" message.

    :param str text: Text to wrap.
    """
    print(f"[ \u2713 ] {text}".encode("utf-8"))


def debug(text: str) -> None:
    """Wrap a "debug" message.

    Intended for debugging sessions.

    :param str text: Text to wrap.
    """
    print(f"[ DEBUG ] {text}")
