"""Functions for making checksums in tests."""

from hashlib import sha256


def checksum_of(content: bytes) -> str:
    """Make the checksum that bunny.net stores for some bytes.

    Args:
        content: The bytes to hash.

    Returns:
        The content's SHA-256, in uppercase hexadecimal.
    """
    return sha256(content).hexdigest().upper()
