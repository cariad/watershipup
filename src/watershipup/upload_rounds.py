"""Functions for upload rounds."""

from collections.abc import Iterable

from .local_file import LocalFile
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


def sort_by_round(
    local_files: Iterable[LocalFile],
) -> tuple[LocalFile, ...]:
    """Put files to upload in the order of their rounds.

    Args:
        local_files: The files to upload.

    Returns:
        Every asset, then every page, then every feed. Files in the same round keep
        their order.
    """
    return tuple(
        sorted(
            local_files,
            key=lambda local_file: round_of(local_file.remote_path).value,
        ),
    )


def sort_for_deletion(
    remote_paths: Iterable[str],
) -> tuple[str, ...]:
    """Put files to delete in the reverse order of their rounds.

    So a feed is never served after the pages that it points at are deleted.

    Args:
        remote_paths: The storage zone paths of the files to delete.

    Returns:
        Every feed, then every page, then every asset. Files in the same round keep
        their order.
    """
    return tuple(
        sorted(
            remote_paths,
            key=lambda remote_path: round_of(remote_path).value,
            reverse=True,
        ),
    )
