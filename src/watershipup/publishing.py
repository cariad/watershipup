"""Functions for publishing."""

from pathlib import Path

from .local_directory import walk_local_directory
from .planning import make_plan
from .publish_report import PublishReport
from .storage_client import StorageClient
from .upload_rounds import sort_by_round, sort_for_deletion


def publish(
    directory: Path,
    *,
    password: str,
    zone: str,
) -> PublishReport:
    """Publish a directory to a storage zone.

    The directory is checked before anything is sent to bunny.net.

    Every new and changed file is uploaded, one at a time, in rounds: every asset, then
    every page, then every feed.

    Once every upload has succeeded, every page and feed in the zone that's no longer in
    the directory is deleted, every feed before every page. Every other file that's no
    longer in the directory is kept.

    Args:
        directory: Path to the directory to publish.
        password: The storage zone's password.
        zone: The storage zone's name.

    Returns:
        What the publish did.

    Raises:
        HiddenPathError: When the directory holds a hidden file or directory, other
            than `.well-known` at its root.
        InvalidNameError: When a name in a file's path would be rejected by bunny.net.
        NoFilesError: When the directory has no files to publish.
        OSError: When the directory, one of its subdirectories, or one of its files
            can't be read.
        RequestFailedError: When bunny.net refuses a request.
        UnicodeEncodeError: When a file's path within the directory isn't valid UTF-8,
            or the password isn't ASCII.
        ValueError: When one of the zone's listings is invalid.
        httpx2.RequestError: When bunny.net can't be reached, its response can't be
            read, or the password has whitespace at either end, or a control character
            other than a tab, such as a line break. That last error's message holds
            the password.
    """
    local_files = walk_local_directory(directory)

    with StorageClient(
        password=password,
        zone=zone,
    ) as client:
        plan = make_plan(
            local_files,
            client.walk_zone(),
        )

        for local_file in sort_by_round(plan.uploads):
            client.upload(
                local_file.local_path,
                local_file.remote_path,
                checksum=local_file.checksum,
            )

        for remote_path in sort_for_deletion(plan.deletions):
            client.delete(remote_path)

    return PublishReport(
        deleted=plan.deletions,
        kept=plan.kept,
        unchanged=plan.unchanged,
        uploaded=tuple(local_file.remote_path for local_file in plan.uploads),
    )
