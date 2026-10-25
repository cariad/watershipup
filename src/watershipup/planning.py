"""Functions for planning a publish."""

from collections.abc import Iterable

from .local_file import LocalFile
from .plan import Plan
from .zone_file import ZoneFile


def make_plan(
    local_files: Iterable[LocalFile],
    zone_files: Iterable[ZoneFile],
) -> Plan:
    """Plan which files to upload, and which to leave alone.

    A file is uploaded unless the zone has one at the same path with the same checksum.

    Paths are case-sensitive.

    Checksums comparisons are case-insensitive.

    A file that doesn't have a checksum in the zone is uploaded again, rather than
    downloading it to hash and check.

    Args:
        local_files: The files in the directory to publish.
        zone_files: The files in the storage zone.

    Returns:
        The plan.
    """
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

    return Plan(
        tuple(uploads),
        tuple(unchanged),
    )
