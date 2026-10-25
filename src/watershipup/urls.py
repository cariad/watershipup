"""Functions for URLs."""

from urllib.parse import quote

STORAGE_HOST = "storage.bunnycdn.com"


def make_zone_url(
    zone: str,
    remote_path: str,
) -> str:
    """Make the storage zone URL for a remote path.

    Args:
        zone: The storage zone's name.
        remote_path: The unencoded remote path.

    Returns:
        URL.

    Raises:
        ValueError: When the path has a "." or ".." segment.
    """
    if {".", ".."} & set(remote_path.split("/")):
        raise ValueError(
            f"Won't make a URL for a path with a dot segment: {remote_path!r}"
        )

    return f"https://{STORAGE_HOST}/{zone}/{quote(remote_path)}"
