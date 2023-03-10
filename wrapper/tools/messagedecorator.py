import io
import os
import sys


def banner(text):
    """A custom simple banner."""
    banner_len = len(text) + 6
    print("\n" + "*" * banner_len)
    print(f"** {text} **")
    print("** by seppzer0" + " " * (banner_len - 17) + " **")
    print("*" * banner_len)
    print("\n", end="")


def note(msgtext):
    """A "note" wrapper."""
    print(f"[ * ] {msgtext}")


def error(msgtext, dont_exit=False):
    """An "error" wrapper."""
    print(f"[ ! ] {msgtext}", file=sys.stderr)
    if not dont_exit:
        sys.exit(1)


def cancel(msgtext):
    """A "cancel" wrapper."""
    print(f"[ ~ ] {msgtext}")
    sys.exit(0)


def done(msgtext):
    """A "done" wrapper."""
    print(f"[ + ] {msgtext}")


def outputstream():
    """Stream output messages."""
    stream = os.getenv("OSTREAM", "screen")
    if stream != "screen":
        sys.stdout = open(stream, "a")
    else:
        sys.stdout = io.TextIOWrapper(open(sys.stdout.fileno(), 'wb', 0), write_through=True)
