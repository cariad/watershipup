"""Functions for upload rounds."""

from .upload_round import UploadRound
from .zone_paths import extension_of

EXTENSION_ROUNDS = {
    "html": UploadRound.PAGES,
    "json": UploadRound.FEEDS,
    "txt": UploadRound.FEEDS,
    "webmanifest": UploadRound.FEEDS,
    "xml": UploadRound.FEEDS,
}
"""The round of each page's and feed's extension, in lowercase."""


def round_of(remote_path: str) -> UploadRound:
    """Find which round a file is uploaded in.

    Args:
        remote_path: The file's storage zone path, like "css/site.css".

    Returns:
        The round that the file's extension puts it in, as `UploadRound` describes.
    """
    return EXTENSION_ROUNDS.get(
        extension_of(remote_path),
        UploadRound.ASSETS,
    )
