"""The `LocalFile` class, which represents a local file to be uploaded."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalFile:
    """A local file to be uploaded.

    Attributes:
        local_path: Local filesystem path.
        remote_path: Intended storage zone path.
        checksum: The file's SHA-256, in uppercase hexadecimal.
    """

    local_path: Path
    remote_path: str
    checksum: str
