"""Functions for making files in tests."""

from pathlib import Path


def touch_files(root: Path, *rel_paths: str) -> None:
    """Make empty files, and any directories they need.

    Args:
        root: Directory to make the files in.
        *rel_paths: Each file's path, relative to `root`.
    """
    for rel_path in rel_paths:
        path = root / rel_path

        path.parent.mkdir(
            exist_ok=True,
            parents=True,
        )

        path.touch()
