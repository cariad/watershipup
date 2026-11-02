"""The CLI command's entry point."""

import os
import signal
import sys
import threading
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence
from pathlib import Path
from types import FrameType

import httpx2

from ..exceptions import WatershipupError
from ..publishing import plan_publish, publish
from ..storage_client import StorageClient
from .tables import tabulate_markdown, tabulate_text
from .version_action import VersionAction

TABULATORS = {
    "text": tabulate_text,
    "markdown": tabulate_markdown,
}
"""The function that tabulates a plan or report in each format."""


class _Terminated(KeyboardInterrupt):
    """SIGTERM, which stops a publish or dry run as Ctrl+C does."""


def _interrupt(signum: int, frame: FrameType | None) -> None:
    """Handle SIGTERM as Ctrl+C is handled.

    Args:
        signum: The signal's number.
        frame: The frame that the signal interrupted.

    Raises:
        _Terminated: Always.
    """
    raise _Terminated


def main(argv: Sequence[str] | None = None) -> int:
    """Run the `watershipup` command.

    The storage zone's password comes only from the `WATERSHIPUP_PASSWORD` environment
    variable, so it stays out of shell history and process lists.

    Args:
        argv: Command-line arguments, without the program's name. Defaults to
            the arguments that the program was run with.

    Returns:
        0 when the publish or dry run succeeded, 1 when it failed, 2 when the password
        is missing or invalid, 130 when Ctrl+C interrupted it, or 143 when SIGTERM did.

    Raises:
        SystemExit: When the arguments are wrong (with 2), or help or the
            version is asked for (with 0).
    """
    parser = ArgumentParser(
        color=False,
        description="Upload a static website to a Bunny Storage zone.",
        prog="watershipup",
    )

    parser.add_argument(
        "--version",
        action=VersionAction,
        default=SUPPRESS,
        help="show the version then exit",
        nargs=0,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what a publish would upload and delete",
    )

    parser.add_argument(
        "--output",
        choices=list(TABULATORS),
        default="text",
        help="the output's format: %(choices)s (default: %(default)s)",
        metavar="FORMAT",
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
    tabulate = TABULATORS[args.output]

    password = os.environ.get("WATERSHIPUP_PASSWORD")

    if not password:
        print(
            f"{parser.prog}: error: WATERSHIPUP_PASSWORD must be set",
            file=sys.stderr,
        )
        return 2

    # h11's error for a header value that it refuses, such as one ending in a line
    # break, holds the value. So the password is checked before it's sent, to keep it
    # out of the error.
    if (
        not password.isascii()
        or not password.isprintable()
        or password != password.strip()
    ):
        print(
            f"{parser.prog}: error: WATERSHIPUP_PASSWORD must be printable ASCII, "
            "with no spaces at either end",
            file=sys.stderr,
        )
        return 2

    # Python's default for SIGTERM kills the process at once, cutting uploads off. So
    # SIGTERM stops the publish or dry run as Ctrl+C does, letting the requests in
    # flight finish.
    #
    # Only the main thread can set a signal's handler.
    handles_sigterm = threading.current_thread() is threading.main_thread()
    previous_handler = signal.getsignal(signal.SIGTERM)

    try:
        # The handler is set inside the block, so a SIGTERM straight after it is set is
        # still caught.
        if handles_sigterm:
            signal.signal(
                signal.SIGTERM,
                _interrupt,
            )

        if args.dry_run:
            with StorageClient(
                password=password,
                zone=args.zone,
            ) as client:
                plan = plan_publish(
                    args.directory,
                    client,
                )

            print(tabulate(plan))

            return 0

        report = publish(
            args.directory,
            password=password,
            zone=args.zone,
        )

        print(tabulate(report))

    except _Terminated:
        print(f"{parser.prog}: error: terminated", file=sys.stderr)
        return 143

    except KeyboardInterrupt:
        print(f"{parser.prog}: error: interrupted", file=sys.stderr)
        return 130

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

    finally:
        if handles_sigterm:
            signal.signal(
                signal.SIGTERM,
                previous_handler,
            )

    return 0
