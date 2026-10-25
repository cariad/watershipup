"""The `UploadRound` enum, which says when a file is uploaded."""

from enum import Enum


class UploadRound(Enum):
    """The round of a publish that a file is uploaded in.

    Each round finishes before the next starts, so a new page never points at an asset
    that isn't uploaded yet, and a new feed never points at a page that isn't.
    """

    ASSETS = 1
    """Every file that isn't a page or a feed, like stylesheets, scripts and images."""

    PAGES = 2
    """`.html` files."""

    FEEDS = 3
    """`.xml`, `.txt`, `.json` and `.webmanifest` files, which can point at pages."""
