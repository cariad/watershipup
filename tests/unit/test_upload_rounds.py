"""Tests for upload rounds."""

from pytest import mark

from tests.local_file_helpers import make_local_file
from watershipup.upload_round import UploadRound
from watershipup.upload_rounds import round_of, sort_by_round, sort_for_deletion


@mark.parametrize(
    ["remote_path", "expect"],
    [
        ("index.html", UploadRound.PAGES),
        ("about/INDEX.Html", UploadRound.PAGES),
        ("feed.xml", UploadRound.FEEDS),
        ("blog/Feed.XML", UploadRound.FEEDS),
        ("robots.txt", UploadRound.FEEDS),
        ("Robots.TXT", UploadRound.FEEDS),
        ("search.json", UploadRound.FEEDS),
        ("search.JSON", UploadRound.FEEDS),
        ("site.webmanifest", UploadRound.FEEDS),
        ("site.WebManifest", UploadRound.FEEDS),
        (".well-known/security.txt", UploadRound.FEEDS),
        (".config.json", UploadRound.FEEDS),
        ("..json", UploadRound.FEEDS),
        ("css/site.css", UploadRound.ASSETS),
        ("photo.JPG", UploadRound.ASSETS),
        ("index.html.gz", UploadRound.ASSETS),
        ("app.js.map", UploadRound.ASSETS),
        ("favicon.ico", UploadRound.ASSETS),
        (".json", UploadRound.ASSETS),
        ("blog/.json", UploadRound.ASSETS),
        ("README", UploadRound.ASSETS),
    ],
)
def test_round_of(
    remote_path: str,
    expect: UploadRound,
) -> None:
    """`round_of` must find the round that a file's extension puts it in."""
    upload_round = round_of(remote_path)
    assert upload_round == expect


def test_sort_by_round() -> None:
    """`sort_by_round` must order files by round, keeping each round's order."""
    local_files = [
        make_local_file("robots.txt"),
        make_local_file("index.html"),
        make_local_file("js/site.js"),
        make_local_file("feed.xml"),
        make_local_file("about.html"),
        make_local_file("css/site.css"),
    ]

    uploads = sort_by_round(local_files)

    expect = (
        make_local_file("js/site.js"),
        make_local_file("css/site.css"),
        make_local_file("index.html"),
        make_local_file("about.html"),
        make_local_file("robots.txt"),
        make_local_file("feed.xml"),
    )

    assert uploads == expect


def test_sort_for_deletion() -> None:
    """`sort_for_deletion` must reverse the rounds, keeping each round's order."""
    remote_paths = [
        "old.html",
        "search.json",
        "css/old.css",
        "rss.xml",
        "blog/first-post.html",
    ]

    deletions = sort_for_deletion(remote_paths)

    expect = (
        "search.json",
        "rss.xml",
        "old.html",
        "blog/first-post.html",
        "css/old.css",
    )

    assert deletions == expect
