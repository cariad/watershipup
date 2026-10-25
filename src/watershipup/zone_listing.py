"""The `ZoneListing` class, which represents one storage zone directory's listing."""

from dataclasses import dataclass

from .zone_file import ZoneFile


@dataclass(frozen=True)
class ZoneListing:
    """One storage zone directory's listing.

    Attributes:
        files: The directory's files.
        directories: The storage zone paths of the directory's subdirectories, each
            ending in "/".
    """

    files: tuple[ZoneFile, ...]
    directories: tuple[str, ...]
