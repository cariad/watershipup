"""Tests for content types."""

from pytest import mark

from watershipup.content_types import content_type_of


@mark.parametrize(
    ["remote_path", "expect"],
    [
        ("site.webmanifest", "application/manifest+json"),
        ("icons/Site.WebManifest", "application/manifest+json"),
        (".webmanifest", None),
        ("site.webmanifest.gz", None),
        ("index.html", None),
    ],
)
def test_content_type_of(
    remote_path: str,
    expect: str | None,
) -> None:
    """`content_type_of` must give a type only to a `.webmanifest` file."""
    content_type = content_type_of(remote_path)
    assert content_type == expect
