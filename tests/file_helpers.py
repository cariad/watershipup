"""Functions for making files in tests."""

from pathlib import Path


def touch_files(root: Path, *rel_paths: str) -> None:
    """Make empty files, and any directories they need.

    Args:
        root: Directory to make the files in.
        *rel_paths: Each file's path, relative to `root`.
    """
    write_files(
        root,
        dict.fromkeys(rel_paths, b""),
    )


def write_files(root: Path, contents: dict[str, bytes]) -> None:
    """Make files with contents, and any directories they need.

    Args:
        root: Directory to make the files in.
        contents: Each file's content, by its path relative to `root`.
    """
    for rel_path, content in contents.items():
        path = root / rel_path

        path.parent.mkdir(
            exist_ok=True,
            parents=True,
        )

        path.write_bytes(content)
