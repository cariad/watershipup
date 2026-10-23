"""The command's `--version` option."""

from argparse import Action, ArgumentParser, Namespace
from collections.abc import Sequence
from importlib.metadata import version
from typing import Any


class VersionAction(Action):
    """Print watershipup's version and exit."""

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        """Print watershipup's version and exit.

        Args:
            parser: The command's parser.
            namespace: The arguments parsed so far.
            values: Nothing, because the option takes no value.
            option_string: The option, such as "--version".
        """
        print(f"{parser.prog} {version('watershipup')}")
        parser.exit()
