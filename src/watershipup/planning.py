"""Functions for planning a publish."""

from collections.abc import Iterable

from .local_file import LocalFile
from .plan import Plan
from .upload_round import UploadRound
from .upload_rounds import round_of
from .zone_file import ZoneFile


def make_plan(
    local_files: Iterable[LocalFile],
    zone_files: Iterable[ZoneFile],
) -> Plan:
    """Plan which files to upload, leave alone, delete, and keep.

    A file is uploaded unless the zone has one at the same path with the same checksum.

    Paths are case-sensitive.

    Checksums comparisons are case-insensitive.

    A file that doesn't have a checksum in the zone is uploaded again, rather than
    downloading it to hash and check.

    A page or feed in the zone that's no longer in the directory is deleted. Any other
    file that's no longer in the directory is kept.

    Args:
        local_files: The files in the directory to publish.
        zone_files: The files in the storage zone.

    Returns:
        The plan.
    """
    local_files = tuple(local_files)
    zone_files = tuple(zone_files)

    zone_checksums = {
        zone_file.path: zone_file.checksum.upper()
        for zone_file in zone_files
        if zone_file.checksum is not None
    }

    uploads: list[LocalFile] = []
    unchanged: list[str] = []

    for local_file in sorted(local_files, key=lambda lf: lf.remote_path):
        # A path that the zone doesn't have, or stores without a checksum, gives
        # `None`, which never matches.
        if zone_checksums.get(local_file.remote_path) == local_file.checksum.upper():
            unchanged.append(local_file.remote_path)
        else:
            uploads.append(local_file)

    local_paths = {local_file.remote_path for local_file in local_files}

    deletions: list[str] = []
    kept: list[str] = []

    for path in sorted(zone_file.path for zone_file in zone_files):
        if path in local_paths:
            continue

        if round_of(path) in (UploadRound.PAGES, UploadRound.FEEDS):
            deletions.append(path)
        else:
            kept.append(path)

    return Plan(
        deletions=tuple(deletions),
        kept=tuple(kept),
        unchanged=tuple(unchanged),
        uploads=tuple(uploads),
    )
