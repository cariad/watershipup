"""The `PublishReport` class, which says what a publish did."""

from dataclasses import dataclass


@dataclass(
    frozen=True,
    kw_only=True,
)
class PublishReport:
    """What a publish did.

    Attributes:
        deleted: The storage zone paths of the pages and feeds deleted, because they
            were no longer in the directory, sorted.
        kept: The storage zone paths of the other files that are no longer in the
            directory, which were kept, sorted.
        unchanged: The storage zone paths of the files left alone, sorted.
        uploaded: The storage zone paths of the files uploaded, sorted.
    """

    deleted: tuple[str, ...]
    kept: tuple[str, ...]
    unchanged: tuple[str, ...]
    uploaded: tuple[str, ...]
