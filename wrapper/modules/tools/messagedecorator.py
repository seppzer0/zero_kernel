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
    """A "note" decorator."""
    print(f"[ * ] {msgtext}")


def error(msgtext, dont_exit=False):
    """An "error" decorator."""
    print(f"[ ! ] {msgtext}", file=sys.stderr)
    if not dont_exit:
        sys.exit(1)


def cancel(msgtext):
    """A "cancel" decorator."""
    print(f"[ ~ ] {msgtext}")
    sys.exit(0)


def done(msgtext):
    """A "done" decorator."""
    print(f"[ + ] {msgtext}")
