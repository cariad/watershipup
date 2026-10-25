"""Functions for local files."""

from hashlib import file_digest
from pathlib import Path
from unicodedata import category

INVALID_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}
"""Unicode categories of the characters that watershipup won't publish in a name."""


def has_invalid_name(relative_posix_path: str) -> bool:
    """Check whether a file's path holds a name that watershipup won't publish.

    Args:
        relative_posix_path: The file's path relative to the directory to publish, with
        forward slashes.

    Returns:
        `True` if any name in the path would be rejected by bunny.net.
    """
    for name in relative_posix_path.split("/"):
        if name != name.strip():
            return True

        if any(category(character) in INVALID_CATEGORIES for character in name):
            return True

    return False


def is_hidden(relative_posix_path: str) -> bool:
    """Check whether a file is hidden, or is in a hidden directory.

    `.well-known` at the root isn't hidden, because sites need it.

    Args:
        relative_posix_path: The file's path relative to the directory to
            publish, with forward slashes, such as "css/.DS_Store".

    Returns:
        Whether any name in the path starts with a dot, apart from
        `.well-known` at the root.
    """
    parts = relative_posix_path.split("/")

    if parts[0] == ".well-known" and len(parts) > 1:
        parts.pop(0)

    return any(part.startswith(".") for part in parts)


def make_checksum(path: Path) -> str:
    """Hash a file's contents.

    Args:
        path: Path to the file to hash.

    Returns:
        The file's SHA-256, in uppercase hexadecimal, as bunny.net stores it.

    Raises:
        OSError: When the file can't be read.
    """
    with path.open("rb") as f:
        try:
            return file_digest(f, "sha256").hexdigest().upper()
        except OSError as error:
            # `open` names the file in its errors, but a failed read doesn't.
            error.filename = str(path)
            raise
