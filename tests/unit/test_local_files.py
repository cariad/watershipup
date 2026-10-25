"""Tests for local files."""

from hashlib import sha256
from pathlib import Path

from pytest import mark

from watershipup.local_files import is_hidden, make_checksum


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
