"""Functions for local directories."""

from pathlib import Path

from mosey import Mosey

from .local_file import LocalFile
from .local_files import make_checksum


def walk_local_directory(
    directory: Path,
) -> tuple[LocalFile, ...]:
    """Find all the files in a directory and its subdirectories.

    Symbolic links, and anything that isn't a regular file, are skipped.

    Each file is read once, to record its checksum.

    Args:
        directory: Path to the directory to walk.

    Returns:
        Every discovered file.

    Raises:
        OSError: When the directory, one of its subdirectories, or one of its
            files can't be read.
        UnicodeEncodeError: When a file's path within the directory isn't
            valid UTF-8.
    """
    builder = Mosey()
    builder.ignore_symlinks()
    walker = builder.build()

    found_files = (
        LocalFile(
            step.path,
            # A path that isn't valid UTF-8 can't be a storage zone path, so
            # encoding it raises `UnicodeEncodeError` before anything is
            # uploaded.
            step.relative_as_posix.encode().decode(),
            make_checksum(step.path),
        )
        for step in walker.walk(directory)
    )

    return tuple(found_files)
