import io
import os
import sys


def banner(text: str) -> None:
    """A custom simple banner.

    :param text: Text to wrap.
    """
    banner_len = len(text) + 6
    print("\n" + "*" * banner_len)
    print(f"** {text} **")
    print("** by seppzer0" + " " * (banner_len - 17) + " **")
    print("*" * banner_len)
    print("\n", end="")


def note(text: str) -> None:
    """A "note" text wrapper.

    :param text: Text to wrap.
    """
    print(f"[ * ] {text}")


def error(text: str, dont_exit: bool = False) -> None:
    """An "error" text wrapper.

    Includes system exit with an error code.

    :param text: Text to wrap.
    """
    print(f"[ ! ] {text}", file=sys.stderr)
    if not dont_exit:
        sys.exit(1)


def cancel(text: str) -> None:
    """A "cancel" text wrapper.

    :param text: Text to wrap.
    """
    print(f"[ ~ ] {text}")
    sys.exit(0)


def done(text: str) -> None:
    """A "done" text wrapper.

    :param text: Text to wrap.
    """
    print(f"[ \u2713 ] {text}")


def debug(text: str) -> None:
    """A "debug" text wrapper.

    Intended for debugging sessions.

    :param text: Text to wrap.
    """
    print(f"[ DEBUG ] {text}")


def outputstream() -> None:
    """Stream output messages."""
    stream = os.getenv("OSTREAM", "screen")
    if stream != "screen":
        sys.stdout = open(stream, "a")
    else:
        sys.stdout = io.TextIOWrapper(open(sys.stdout.fileno(), 'wb', 0), write_through=True)
