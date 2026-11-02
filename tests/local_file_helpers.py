"""Functions for making files to upload in tests."""

from pathlib import Path

from tests.checksum_helpers import checksum_of
from watershipup.local_file import LocalFile


def make_local_file(
    remote_path: str,
    content: bytes = b"made-up content",
) -> LocalFile:
    """Make a file to upload, with a made-up local path.

    Args:
        remote_path: The file's storage zone path.
        content: The file's made-up content.

    Returns:
        The file to upload.
    """
    return LocalFile(
        Path("public") / remote_path,
        remote_path,
        checksum_of(content),
    )
