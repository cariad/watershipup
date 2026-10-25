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

    expect = Plan((), ("index.html",))

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

    expect = Plan((), ("index.html",))

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

    expect = Plan((local_file,), ())

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

    expect = Plan((a, b), ("c.css", "d.css"))

    assert plan == expect


def test_make_plan_uploads_changed_file() -> None:
    """`make_plan` must upload a file whose checksum differs from the zone's."""
    index = _local_file("index.html", b"made-up new index")

    plan = make_plan(
        [index],
        [ZoneFile("index.html", checksum_of(b"made-up old index"), "")],
    )

    expect = Plan((index,), ())

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

    expect = Plan((index,), ())

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
        (index,),
        (),
    )

    assert plan == expect
