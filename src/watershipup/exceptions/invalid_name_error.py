"""The `InvalidNameError` class, raised when a file's name can't be published."""

from pathlib import Path

from .watershipup_error import WatershipupError


class InvalidNameError(WatershipupError):
    """Raised when a file's path holds a name that bunny.net would reject.

    Attributes:
        path: Path to the first file found with an invalid name, or file in a directory
            with an invalid name.
    """

    def __init__(self, path: Path) -> None:
        """Describe the file with an invalid name.

        Args:
            path: Path to the first file found with an invalid name, or file in a
                directory with an invalid name.
        """
        super().__init__(path)
        self.path = path

    def __str__(self) -> str:
        """Name the file, with any control character escaped."""
        name = str(self.path)
        return (
            "Won't publish a file whose path has a name that bunny.net would "
            f"reject: {name!r}"
        )
