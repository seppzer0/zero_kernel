def print_banner(text: str) -> None:
    """Custom banner print out.

    :param str text: Text to wrap.
    """
    banner_len = len(text) + 6
    print("\n" + "*" * banner_len)
    print(f"** {text} **")
    print("** by seppzer0" + " " * (banner_len - 17) + " **")
    print("*" * banner_len)
    print("\n", end="")
