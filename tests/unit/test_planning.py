"""Tests for planning a publish."""

from pathlib import Path
from unicodedata import normalize

from pytest import mark

from tests.checksum_helpers import checksum_of
from watershipup.local_file import LocalFile
from watershipup.plan import Plan
from watershipup.planning import make_plan
from watershipup.zone_file import ZoneFile


def _local_file(remote_path: str, content: bytes) -> LocalFile:
    """Make a file to upload, with a made-up local path.

    Args:
        remote_path: The file's storage zone path.
        content: The file's made-up content.

    Returns:
        The file to upload.
    """
    return LocalFile(
        Path("public") / remote_path,
        remote_path,
        checksum_of(content),
    )


def test_make_plan_accepts_iterators() -> None:
    """`make_plan` must plan from iterators, which it can read only once."""
    index = _local_file(
        "index.html",
        b"made-up index",
    )

    plan = make_plan(
        iter([index]),
        iter(
            [
                ZoneFile(
                    "index.html",
                    checksum_of(b"made-up index"),
                    "",
                ),
                ZoneFile(
                    "old.html",
                    checksum_of(b"made-up old page"),
                    "",
                ),
            ],
        ),
    )

    expect = Plan(
        deletions=("old.html",),
        kept=(),
        unchanged=("index.html",),
        uploads=(),
    )

    assert plan == expect


@mark.parametrize(
    "zone_path",
    [
        "old.html",
        "OLD.HTML",
        "feed.xml",
        "blog/Feed.Xml",
        "notes.txt",
        "Notes.TXT",
        "search.json",
        "Search.JSON",
        "site.webmanifest",
        "Site.WebManifest",
    ],
)
def test_make_plan_deletes_pages_and_feeds(zone_path: str) -> None:
    """`make_plan` must delete a page or feed that's no longer in the directory."""
    plan = make_plan(
        [],
        [ZoneFile(zone_path, checksum_of(b"made-up old file"), "")],
    )

    expect = Plan(
        deletions=(zone_path,),
        kept=(),
        unchanged=(),
        uploads=(),
    )

    assert plan == expect


@mark.parametrize(
    ["local_checksum", "zone_checksum"],
    [
        ("ABC123", "abc123"),
        ("abc123", "ABC123"),
    ],
)
def test_make_plan_ignores_checksum_case(
    local_checksum: str,
    zone_checksum: str,
) -> None:
    """`make_plan` must match checksums whatever their case."""
    plan = make_plan(
        [LocalFile(Path("public/index.html"), "index.html", local_checksum)],
        [ZoneFile("index.html", zone_checksum, "")],
    )

    expect = Plan(
        deletions=(),
        kept=(),
        unchanged=("index.html",),
        uploads=(),
    )

    assert plan == expect


@mark.parametrize(
    "zone_path",
    [
        "img/photo.jpg",
        "css/site.css",
        "js/app.js",
        "guide.pdf",
        "favicon.ico",
        "js/app.js.map",
        "README",
    ],
)
def test_make_plan_keeps_other_files(zone_path: str) -> None:
    """`make_plan` must keep an asset that's no longer in the directory."""
    plan = make_plan(
        [],
        [
            ZoneFile(
                zone_path,
                checksum_of(b"made-up old file"),
                "",
            ),
        ],
    )

    expect = Plan(
        deletions=(),
        kept=(zone_path,),
        unchanged=(),
        uploads=(),
    )

    assert plan == expect


def test_make_plan_leaves_unchanged_file() -> None:
    """`make_plan` must leave a file alone when the zone has the same one."""
    index = _local_file(
        "index.html",
        b"made-up index",
    )

    plan = make_plan(
        [
            index,
        ],
        [
            ZoneFile(
                "index.html",
                checksum_of(b"made-up index"),
                "",
            ),
        ],
    )

    expect = Plan(
        deletions=(),
        kept=(),
        unchanged=("index.html",),
        uploads=(),
    )

    assert plan == expect


@mark.parametrize(
    ["local_path", "zone_path"],
    [
        ("Index.html", "index.html"),
        (
            normalize("NFC", "café.html"),
            normalize("NFD", "café.html"),
        ),
    ],
)
def test_make_plan_matches_paths_exactly(local_path: str, zone_path: str) -> None:
    """`make_plan` must upload a file whose path differs by case or Unicode form."""
    local_file = _local_file(local_path, b"made-up page")

    plan = make_plan(
        [local_file],
        [ZoneFile(zone_path, checksum_of(b"made-up page"), "")],
    )

    expect = Plan(
        deletions=(zone_path,),
        kept=(),
        unchanged=(),
        uploads=(local_file,),
    )

    assert plan == expect


def test_make_plan_sorts_by_path() -> None:
    """`make_plan` must sort its uploads and unchanged files by storage zone path."""
    # "-" sorts before "/" in a string, but a `Path` sorts "a/b.html" first.
    a = _local_file("a-b.html", b"made-up a-b")
    b = _local_file("a/b.html", b"made-up a/b")
    c = _local_file("c.css", b"made-up c")
    d = _local_file("d.css", b"made-up d")

    plan = make_plan(
        [d, b, c, a],
        [
            ZoneFile("d.css", checksum_of(b"made-up d"), ""),
            ZoneFile("c.css", checksum_of(b"made-up c"), ""),
        ],
    )

    expect = Plan(
        deletions=(),
        kept=(),
        unchanged=("c.css", "d.css"),
        uploads=(a, b),
    )

    assert plan == expect


def test_make_plan_sorts_deletions_and_kept() -> None:
    """`make_plan` must sort the files it deletes and keeps by storage zone path."""
    plan = make_plan(
        [],
        [
            ZoneFile("b.html", checksum_of(b"made-up b"), ""),
            ZoneFile("d.css", checksum_of(b"made-up d"), ""),
            ZoneFile("a.html", checksum_of(b"made-up a"), ""),
            ZoneFile("c.css", checksum_of(b"made-up c"), ""),
        ],
    )

    expect = Plan(
        deletions=("a.html", "b.html"),
        kept=("c.css", "d.css"),
        unchanged=(),
        uploads=(),
    )

    assert plan == expect


def test_make_plan_uploads_changed_file() -> None:
    """`make_plan` must upload a file whose checksum differs from the zone's."""
    index = _local_file("index.html", b"made-up new index")

    plan = make_plan(
        [index],
        [ZoneFile("index.html", checksum_of(b"made-up old index"), "")],
    )

    expect = Plan(
        deletions=(),
        kept=(),
        unchanged=(),
        uploads=(index,),
    )

    assert plan == expect


def test_make_plan_uploads_file_without_checksum() -> None:
    """`make_plan` must upload a file that the zone stores without a checksum."""
    index = _local_file(
        "index.html",
        b"made-up index",
    )

    plan = make_plan(
        [index],
        [ZoneFile("index.html", None, "")],
    )

    expect = Plan(
        deletions=(),
        kept=(),
        unchanged=(),
        uploads=(index,),
    )

    assert plan == expect


def test_make_plan_uploads_new_file() -> None:
    """`make_plan` must upload a file that isn't in the zone."""
    index = _local_file(
        "index.html",
        b"made-up index",
    )

    plan = make_plan(
        [index],
        [],
    )

    expect = Plan(
        deletions=(),
        kept=(),
        unchanged=(),
        uploads=(index,),
    )

    assert plan == expect
