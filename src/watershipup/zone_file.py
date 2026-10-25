"""The `ZoneFile` class, which represents a file in a storage zone."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneFile:
    """A file in a storage zone, as its directory's listing describes it.

    Attributes:
        path: Path within the storage zone.
        checksum: The file's SHA-256, in uppercase hexadecimal, if it has one.
        content_type: The file's stored type, or "" when it was uploaded without one.
    """

    path: str
    checksum: str | None
    content_type: str
