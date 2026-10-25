"""The CLI command's entry point."""

import os
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import httpx2

from ..exceptions import WatershipupError
from ..publishing import publish
from .summaries import summarise
from .version_action import VersionAction


def main(argv: Sequence[str] | None = None) -> int:
    """Run the `watershipup` command.

    The storage zone's password comes only from the `WATERSHIPUP_PASSWORD` environment
    variable, so it stays out of shell history and process lists.

    Args:
        argv: Command-line arguments, without the program's name. Defaults to
            the arguments that the program was run with.

    Returns:
        0 when the publish succeeded, 1 when it failed, or 2 when the password is
        missing.

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

    parser.add_argument(
        "--zone",
        help="the storage zone's name",
        metavar="NAME",
        required=True,
    )

    parser.add_argument(
        "directory",
        help="the directory to publish",
        metavar="DIRECTORY",
        type=Path,
    )

    args = parser.parse_args(argv)

    password = os.environ.get("WATERSHIPUP_PASSWORD")

    if not password:
        print(
            f"{parser.prog}: error: WATERSHIPUP_PASSWORD must be set",
            file=sys.stderr,
        )
        return 2

    try:
        report = publish(
            args.directory,
            password=password,
            zone=args.zone,
        )
    # `httpx2.InvalidURL` isn't an `httpx2.RequestError`. It's raised for a zone's name
    # that can't be part of a URL, like one with a line break.
    except (
        WatershipupError,
        httpx2.InvalidURL,
        httpx2.RequestError,
        OSError,
        ValueError,
    ) as error:
        print(f"{parser.prog}: error: {error}", file=sys.stderr)
        return 1

    # The zone's listings can hold any name, so paths are printed with control
    # characters escaped.
    for path in report.uploaded:
        print(f"Uploaded {path!r}")

    for path in report.deleted:
        print(f"Deleted {path!r}")

    for path in report.kept:
        print(f"Kept {path!r}, which is no longer in the directory")

    print(summarise(report))

    return 0
