import io
import os
import sys


def banner(text: str) -> None:
    """A custom simple banner.

    :param str text: Text to wrap.
    """
    banner_len = len(text) + 6
    print("\n" + "*" * banner_len)
    print(f"** {text} **")
    print("** by seppzer0" + " " * (banner_len - 17) + " **")
    print("*" * banner_len)
    print("\n", end="")


def note(text: str) -> None:
    """A "note" wrapper.

    :param str text: Text to wrap.
    """
    print(f"[ * ] {text}")


def error(text: str, dont_exit: bool = False) -> None:
    """An "error" wrapper.

    :param str text: Text to wrap.
    """
    print(f"[ ! ] {text}", file=sys.stderr)
    if not dont_exit:
        sys.exit(1)


def cancel(text: str) -> None:
    """A "cancel" wrapper.

    :param str text: Text to wrap.
    """
    print(f"[ ~ ] {text}")
    sys.exit(0)


def done(text: str) -> None:
    """A "done" wrapper.

    :param str text: Text to wrap.
    """
    print(f"[ + ] {text}")


def outputstream() -> None:
    """Stream output messages."""
    stream = os.getenv("OSTREAM", "screen")
    if stream != "screen":
        sys.stdout = open(stream, "a")
    else:
        sys.stdout = io.TextIOWrapper(open(sys.stdout.fileno(), 'wb', 0), write_through=True)
