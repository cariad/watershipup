"""Functions for storage zone listings."""

import json
from typing import cast
from unicodedata import category

from .zone_file import ZoneFile
from .zone_listing import ZoneListing


def is_valid_directory(directory: str) -> bool:
    """Check whether a path can be a storage zone directory's path.

    Args:
        directory: "" for the zone's root, or a path that ends with "/".

    Returns:
        `True` if the path is valid.
    """
    # The zone's root.
    if not directory:
        return True

    if not directory.endswith("/"):
        return False

    names = directory.removesuffix("/").split("/")

    return all(is_valid_name(name) for name in names)


def is_valid_name(name: str) -> bool:
    """Check whether a name can be part of a storage zone path.

    Args:
        name: A file's or directory's name.

    Returns:
        `False` if the name is empty, ".", "..", holds a "/", or holds a lone
        surrogate, which can't be encoded in a request's path.
    """
    return (
        name not in ("", ".", "..")
        and "/" not in name
        and not any(category(character) == "Cs" for character in name)
    )


def parse_listing(
    directory: str,
    content: bytes,
) -> ZoneListing:
    """Parse one directory's listing.

    Each path is the listed directory plus the entry's `ObjectName`. The entry's `Path`,
    and a directory's `Checksum` and `ContentType`, are never read.

    Args:
        directory: The directory that was listed: "" for the zone's root, or a path
            ending in "/", like "css/".
        content: The listing's body; a JSON array of the directory's files and
            subdirectories.

    Returns:
        The directory's files and subdirectories.

    Raises:
        ValueError: When the content is invalid.
    """
    entries: object = json.loads(content)

    if not isinstance(entries, list):
        raise ValueError(f"Listing of {directory!r} isn't a JSON array")

    files: list[ZoneFile] = []
    directories: list[str] = []
    names: set[str] = set()

    for entry in cast(list[object], entries):
        fields = cast(dict[str, object], entry) if isinstance(entry, dict) else {}

        name = fields.get("ObjectName")
        is_directory = fields.get("IsDirectory")

        if not isinstance(name, str):
            raise ValueError(
                f"Listing of {directory!r} has an entry without a string ObjectName"
            )

        if not is_valid_name(name):
            raise ValueError(
                f"Listing of {directory!r} has an invalid ObjectName: {name!r}"
            )

        if name in names:
            raise ValueError(f"Listing of {directory!r} has {name!r} more than once")

        names.add(name)

        if not isinstance(is_directory, bool):
            raise ValueError(
                f"Listing of {directory!r} has an invalid IsDirectory for {name!r}"
            )

        path = directory + name

        if is_directory:
            directories.append(f"{path}/")
            continue

        checksum = fields.get("Checksum")
        content_type = fields.get("ContentType")

        if not isinstance(checksum, str | None):
            raise ValueError(
                f"Listing of {directory!r} has an invalid Checksum for {name!r}"
            )

        if not isinstance(content_type, str | None):
            raise ValueError(
                f"Listing of {directory!r} has an invalid ContentType for {name!r}"
            )

        zone_file = ZoneFile(
            path,
            checksum.upper() if checksum else None,
            content_type or "",
        )

        files.append(zone_file)

    return ZoneListing(
        tuple(files),
        tuple(directories),
    )
