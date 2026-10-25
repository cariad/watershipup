"""The `Plan` class, which says what a publish will do."""

from dataclasses import dataclass

from .local_file import LocalFile


@dataclass(
    frozen=True,
    kw_only=True,
)
class Plan:
    """What a publish will do with each file.

    Attributes:
        deletions: The storage zone paths of the pages and feeds to delete, because
            they're no longer in the directory, sorted.
        kept: The storage zone paths of the files that are no longer in the directory,
            but kept, sorted.
        unchanged: The storage zone paths of the files to leave alone, sorted.
        uploads: The files to upload, sorted by storage zone path.
    """

    deletions: tuple[str, ...]
    kept: tuple[str, ...]
    unchanged: tuple[str, ...]
    uploads: tuple[LocalFile, ...]
