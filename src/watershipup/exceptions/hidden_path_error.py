"""The `HiddenPathError` class, raised when a hidden file or directory is found."""

from pathlib import Path

from .watershipup_error import WatershipupError


class HiddenPathError(WatershipupError):
    """Raised when the directory to publish holds a hidden file or directory.

    Everything watershipup uploads is public, so a hidden file such as `.env`, or a
    hidden directory such as `.git`, is never published.

    The root's `.well-known` directory is the only exception, because sites need it.

    Attributes:
        path: Path to the first hidden file or directory found.
    """

    def __init__(self, path: Path) -> None:
        """Describe the hidden file or directory.

        Args:
            path: Path to the first hidden file or directory found.
        """
        super().__init__(path)
        self.path = path

    def __str__(self) -> str:
        """Name the hidden file or directory."""
        name = str(self.path)
        return f"Won't publish a hidden file or directory: {name!r}"
