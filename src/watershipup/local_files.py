"""Functions for local files."""

from hashlib import file_digest
from pathlib import Path


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
