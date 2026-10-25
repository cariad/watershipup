"""Functions for content types."""

from .zone_paths import extension_of

EXTENSION_CONTENT_TYPES = {
    "webmanifest": "application/manifest+json",
}
"""The type that each extension's files are uploaded with, by lowercase extension."""


def content_type_of(remote_path: str) -> str | None:
    """Find the custom type that a file is uploaded with, if it has one.

    A path without a custom type uses bunny.net's default.

    Args:
        remote_path: The file's storage zone path.

    Returns:
        The custom type for the file's extension, or `None` to use bunny.net's default.
    """
    return EXTENSION_CONTENT_TYPES.get(extension_of(remote_path))
