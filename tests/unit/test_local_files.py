"""Tests for local files."""

from hashlib import sha256
from pathlib import Path

from pytest import mark

from watershipup.local_files import has_invalid_name, is_hidden, make_checksum


@mark.parametrize(
    "path",
    [
        " index.html",
        "index.html ",
        " css/site.css",
        "css /site.css",
        "css/ site.css",
        "index.html\u00a0",
        "\u3000index.html",
        "tab\there.html",
        "line\nbreak.html",
        "delete\x7f.html",
        "css\t/site.css",
        "css/tab\t.css",
        "line\u2028break.html",
        "paragraph\u2029break.html",
        "\ufeffindex.html",
        "zero\u200bwidth.html",
    ],
)
def test_has_invalid_name(path: str) -> None:
    """`has_invalid_name` must be true for each kind of invalid name."""
    invalid = has_invalid_name(path)
    assert invalid


@mark.parametrize(
    "path",
    [
        "index.html",
        "css/site.css",
        "about us.html",
        "café/menu.html",
    ],
)
def test_has_invalid_name_when_valid(path: str) -> None:
    """`has_invalid_name` must be false for a name that bunny.net stores."""
    invalid = has_invalid_name(path)
    assert not invalid


@mark.parametrize(
    "path",
    [
        ".env",
        ".git/config",
        "css/.DS_Store",
        "css/.cache/site.css",
        ".well-known/.env",
        "css/.well-known/security.txt",
    ],
)
def test_is_hidden(path: str) -> None:
    """`is_hidden` must be true for a hidden file or a file in a hidden directory."""
    hidden = is_hidden(path)
    assert hidden


@mark.parametrize(
    "path",
    [
        "index.html",
        "css/site.min.css",
        ".well-known/security.txt",
    ],
)
def test_is_hidden_when_visible(path: str) -> None:
    """`is_hidden` must be false for a file that isn't hidden."""
    hidden = is_hidden(path)
    assert not hidden


def test_make_checksum(tmp_path: Path) -> None:
    """`make_checksum` must return the file's SHA-256 in uppercase."""
    path = tmp_path / "index.html"
    path.write_bytes(b"made-up content")

    checksum = make_checksum(path)
    expect = sha256(b"made-up content").hexdigest().upper()

    assert checksum == expect
