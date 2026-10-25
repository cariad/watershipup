"""Functions for upload rounds."""

from .upload_round import UploadRound

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

    A file's extension is the part of its name after the last dot, unless that dot
    starts the name. Its case doesn't matter.

    Args:
        remote_path: The file's storage zone path, like "css/site.css".

    Returns:
        The round that the file's extension puts it in, as `UploadRound` describes.
    """
    leaf = remote_path.rsplit("/", 1)[-1]
    dot = leaf.rfind(".")
    extension = leaf[dot + 1 :].lower() if dot > 0 else ""

    return EXTENSION_ROUNDS.get(
        extension,
        UploadRound.ASSETS,
    )
