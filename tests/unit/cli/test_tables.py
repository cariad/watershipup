"""Tests for tabulating a plan or a publish report."""

from pytest import mark

from tests.local_file_helpers import make_local_file
from watershipup.cli.tables import tabulate_markdown, tabulate_text
from watershipup.local_file import LocalFile
from watershipup.plan import Plan
from watershipup.publish_report import PublishReport


def _uploads(*remote_paths: str) -> tuple[LocalFile, ...]:
    """Make files to upload, with made-up local paths and content.

    Args:
        *remote_paths: The files' storage zone paths.

    Returns:
        The files to upload.
    """
    return tuple(make_local_file(remote_path) for remote_path in remote_paths)


@mark.parametrize(
    ["source", "expect"],
    [
        (
            Plan(
                deletions=("blog/old.html", "old.xml"),
                kept=("img/old.png",),
                unchanged=("about.html",),
                uploads=_uploads(
                    "css/site.css",
                    "feed.xml",
                    "img/logo.png",
                    "index.html",
                ),
            ),
            "### Assets\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `css/site.css` | Upload |\n"
            "| `img/logo.png` | Upload |\n"
            "\n"
            "### Pages\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `blog/old.html` | Delete |\n"
            "| `index.html` | Upload |\n"
            "\n"
            "### Feeds\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `feed.xml` | Upload |\n"
            "| `old.xml` | Delete |",
        ),
        (
            Plan(
                deletions=(),
                kept=(),
                unchanged=("index.html",),
                uploads=_uploads(
                    "css/site.css",
                    "feed.xml",
                ),
            ),
            "### Assets\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `css/site.css` | Upload |\n"
            "\n"
            "### Feeds\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `feed.xml` | Upload |",
        ),
        (
            Plan(
                deletions=("old.html",),
                kept=(),
                unchanged=("index.html",),
                uploads=(),
            ),
            "### Pages\n\n| Path | Change |\n| - | - |\n| `old.html` | Delete |",
        ),
        (
            Plan(
                deletions=(),
                kept=("img/old.png",),
                unchanged=("index.html",),
                uploads=(),
            ),
            "No changes.",
        ),
        (
            PublishReport(
                deleted=("blog/old.html", "old.xml"),
                kept=("img/old.png",),
                unchanged=("about.html",),
                uploaded=(
                    "css/site.css",
                    "feed.xml",
                    "img/logo.png",
                    "index.html",
                ),
            ),
            "### Assets\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `css/site.css` | Uploaded |\n"
            "| `img/logo.png` | Uploaded |\n"
            "\n"
            "### Pages\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `blog/old.html` | Deleted |\n"
            "| `index.html` | Uploaded |\n"
            "\n"
            "### Feeds\n"
            "\n"
            "| Path | Change |\n"
            "| - | - |\n"
            "| `feed.xml` | Uploaded |\n"
            "| `old.xml` | Deleted |",
        ),
    ],
)
def test_tabulate_markdown(
    source: Plan | PublishReport,
    expect: str,
) -> None:
    """`tabulate_markdown` must tabulate each round's uploads and deletions."""
    markdown = tabulate_markdown(source)
    assert markdown == expect


@mark.parametrize(
    ["source", "expect"],
    [
        (
            Plan(
                deletions=("blog/old.html", "old.xml"),
                kept=("img/old.png",),
                unchanged=("about.html",),
                uploads=_uploads(
                    "css/site.css",
                    "feed.xml",
                    "img/logo.png",
                    "index.html",
                ),
            ),
            "Assets\n"
            "\n"
            "Path           Change\n"
            "css/site.css   Upload\n"
            "img/logo.png   Upload\n"
            "\n"
            "Pages\n"
            "\n"
            "Path           Change\n"
            "blog/old.html  Delete\n"
            "index.html     Upload\n"
            "\n"
            "Feeds\n"
            "\n"
            "Path           Change\n"
            "feed.xml       Upload\n"
            "old.xml        Delete",
        ),
        (
            Plan(
                deletions=(),
                kept=(),
                unchanged=("index.html",),
                uploads=_uploads(
                    "css/site.css",
                    "feed.xml",
                ),
            ),
            "Assets\n"
            "\n"
            "Path          Change\n"
            "css/site.css  Upload\n"
            "\n"
            "Feeds\n"
            "\n"
            "Path          Change\n"
            "feed.xml      Upload",
        ),
        (
            Plan(
                deletions=(),
                kept=(),
                unchanged=(),
                uploads=_uploads("a.c"),
            ),
            "Assets\n\nPath  Change\na.c   Upload",
        ),
        (
            Plan(
                deletions=("old.html",),
                kept=(),
                unchanged=("index.html",),
                uploads=(),
            ),
            "Pages\n\nPath      Change\nold.html  Delete",
        ),
        (
            Plan(
                deletions=(),
                kept=("img/old.png",),
                unchanged=("index.html",),
                uploads=(),
            ),
            "No changes.",
        ),
        (
            PublishReport(
                deleted=("blog/old.html", "old.xml"),
                kept=("img/old.png",),
                unchanged=("about.html",),
                uploaded=(
                    "css/site.css",
                    "feed.xml",
                    "img/logo.png",
                    "index.html",
                ),
            ),
            "Assets\n"
            "\n"
            "Path           Change\n"
            "css/site.css   Uploaded\n"
            "img/logo.png   Uploaded\n"
            "\n"
            "Pages\n"
            "\n"
            "Path           Change\n"
            "blog/old.html  Deleted\n"
            "index.html     Uploaded\n"
            "\n"
            "Feeds\n"
            "\n"
            "Path           Change\n"
            "feed.xml       Uploaded\n"
            "old.xml        Deleted",
        ),
    ],
)
def test_tabulate_text(
    source: Plan | PublishReport,
    expect: str,
) -> None:
    """`tabulate_text` must tabulate each round's uploads and deletions."""
    text = tabulate_text(source)
    assert text == expect
