"""The `NoFilesError` class, raised when there are no files to publish."""

from pathlib import Path

from .watershipup_error import WatershipupError


class NoFilesError(WatershipupError):
    """Raised when the directory to publish has no files to publish.

    Publishing an empty directory would upload nothing, but delete every page
    and feed in the storage zone, so a site generator's empty output must
    never be published by mistake.

    Attributes:
        directory: Path to the directory to publish.
    """

    def __init__(self, directory: Path) -> None:
        """Describe the directory with no files to publish.

        Args:
            directory: Path to the directory to publish.
        """
        super().__init__(directory)
        self.directory = directory

    def __str__(self) -> str:
        """Name the directory with no files to publish."""
        name = str(self.directory)
        return f"No files to publish in {name!r}"
