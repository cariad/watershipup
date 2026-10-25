"""Tests for upload rounds."""

from pytest import mark

from watershipup.upload_round import UploadRound
from watershipup.upload_rounds import round_of


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
