"""Functions for local directories."""

from pathlib import Path

from mosey import Mosey

from .exceptions import HiddenPathError, NoFilesError
from .local_file import LocalFile
from .local_files import is_hidden, make_checksum


def walk_local_directory(
    directory: Path,
) -> tuple[LocalFile, ...]:
    """Find all the files in a directory and its subdirectories.

    Symbolic links, and anything that isn't a regular file, are skipped.

    Each file is read once, to record its checksum.

    Hidden files aren't read.

    Args:
        directory: Path to the directory to walk.

    Returns:
        Every discovered file.

    Raises:
        HiddenPathError: When the directory holds any hidden file or
            directory, other than `.well-known` at its root.
        NoFilesError: When the directory has no files to publish.
        OSError: When the directory, one of its subdirectories, or one of its
            files can't be read.
        UnicodeEncodeError: When a file's path within the directory isn't
            valid UTF-8.
    """
    builder = Mosey()
    builder.ignore_symlinks()
    walker = builder.build()

    found_files: list[LocalFile] = []

    for step in walker.walk(directory):
        # A path that isn't valid UTF-8 can't be a storage zone path, so
        # encoding it raises `UnicodeEncodeError` before anything is uploaded.
        remote_path = step.relative_as_posix.encode().decode()

        if is_hidden(remote_path):
            raise HiddenPathError(step.path)

        local_file = LocalFile(
            step.path,
            remote_path,
            make_checksum(step.path),
        )

        found_files.append(local_file)

    if not found_files:
        raise NoFilesError(directory)

    return tuple(found_files)
