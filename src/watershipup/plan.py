"""The `Plan` class, which says what a publish will do."""

from dataclasses import dataclass

from .local_file import LocalFile


@dataclass(frozen=True)
class Plan:
    """What a publish will do with each file.

    Attributes:
        uploads: The files to upload, sorted by storage zone path.
        unchanged: The storage zone paths of the files to leave alone, sorted.
    """

    uploads: tuple[LocalFile, ...]
    unchanged: tuple[str, ...]
