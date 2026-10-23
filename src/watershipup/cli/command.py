"""The CLI command's entry point."""

import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence
from typing import Any

from .version_action import VersionAction


def main(argv: Sequence[str] | None = None) -> int:
    """Run the `watershipup` command.

    So far, it only shows its help and its version.

    Args:
        argv: Command-line arguments, without the program's name. Defaults to
            the arguments that the program was run with.

    Returns:
        0.

    Raises:
        SystemExit: When the arguments are wrong (with 2), or help or the
            version is asked for (with 0).
    """
    options: dict[str, Any] = {}

    # Don't print in colour.
    #
    # `argparse` doesn't accept this option before 3.14.
    if sys.version_info >= (3, 14):
        options = {
            **options,
            "color": False,
        }

    parser = ArgumentParser(
        description="Upload a static website to a Bunny Storage zone.",
        prog="watershipup",
        **options,
    )

    parser.add_argument(
        "--version",
        action=VersionAction,
        default=SUPPRESS,
        help="show the version then exit",
        nargs=0,
    )

    parser.parse_args(argv)
    return 0
