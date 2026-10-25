"""Tests for storage zone paths."""

from pytest import mark

from watershipup.zone_paths import extension_of


@mark.parametrize(
    ["remote_path", "expect"],
    [
        ("css/site.css", "css"),
        ("Photo.JPG", "jpg"),
        ("index.html.gz", "gz"),
        (".config.json", "json"),
        ("..json", "json"),
        (".json", ""),
        ("blog/.json", ""),
        ("README", ""),
        ("notes.", ""),
    ],
)
def test_extension_of(
    remote_path: str,
    expect: str,
) -> None:
    """`extension_of` must find a file's extension, in lowercase."""
    extension = extension_of(remote_path)
    assert extension == expect
