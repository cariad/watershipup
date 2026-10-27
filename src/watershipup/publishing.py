"""Functions for publishing."""

from functools import partial
from itertools import groupby
from pathlib import Path

from .concurrency import run_all
from .local_directory import walk_local_directory
from .planning import make_plan
from .publish_report import PublishReport
from .storage_client import StorageClient
from .upload_rounds import round_of, sort_by_round, sort_for_deletion

MAX_CONCURRENCY = 16
"""The most uploads or deletes at once, which keeps deletes under bunny.net's limit of
30 at once."""


def publish(
    directory: Path,
    *,
    concurrency: int = MAX_CONCURRENCY,
    password: str,
    zone: str,
) -> PublishReport:
    """Publish a directory to a storage zone.

    The directory is checked before anything is sent to bunny.net.

    Every new and changed file is uploaded in rounds: every asset, then every page, then
    every feed. Each round's uploads run at the same time, and a round finishes before
    the next starts.

    Once every upload has succeeded, every page and feed in the zone that's no longer in
    the directory is deleted, every feed before every page. Each round's deletes run at
    the same time. Every other file that's no longer in the directory is kept.

    A request that fails in a way that might not last, like a dropped connection or a
    503, is sent again, up to 5 attempts in all, with a warning logged before each wait.

    Args:
        directory: Path to the directory to publish.
        concurrency: The most uploads or deletes at once, from 1 to `MAX_CONCURRENCY`.
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
        RequestFailedError: When bunny.net refuses a request, after any retries.
        UnicodeEncodeError: When a file's path within the directory isn't valid UTF-8,
            or the password isn't ASCII.
        ValueError: When `concurrency` is out of range, or one of the zone's listings
            is invalid.
        httpx2.RequestError: When bunny.net can't be reached, its response can't be
            read, or the password has whitespace at either end, or a control character
            other than a tab, such as a line break. That last error's message holds
            the password.
    """
    if not 1 <= concurrency <= MAX_CONCURRENCY:
        raise ValueError(
            f"Concurrency must be 1 to {MAX_CONCURRENCY}: {concurrency!r}",
        )

    local_files = walk_local_directory(directory)

    # Every thread shares the client and its pool of connections.
    with StorageClient(
        password=password,
        zone=zone,
    ) as client:
        plan = make_plan(
            local_files,
            client.walk_zone(),
        )

        # The files are sorted by round, so each group is one whole round.
        for _, round_files in groupby(
            sort_by_round(plan.uploads),
            key=lambda local_file: round_of(local_file.remote_path),
        ):
            uploads = [
                partial(
                    client.upload,
                    local_file.local_path,
                    local_file.remote_path,
                    checksum=local_file.checksum,
                )
                for local_file in round_files
            ]

            run_all(
                uploads,
                concurrency,
            )

        for _, round_paths in groupby(
            sort_for_deletion(plan.deletions),
            key=round_of,
        ):
            deletes = [
                partial(
                    client.delete,
                    remote_path,
                )
                for remote_path in round_paths
            ]

            run_all(
                deletes,
                concurrency,
            )

    return PublishReport(
        deleted=plan.deletions,
        kept=plan.kept,
        unchanged=plan.unchanged,
        uploaded=tuple(local_file.remote_path for local_file in plan.uploads),
    )
