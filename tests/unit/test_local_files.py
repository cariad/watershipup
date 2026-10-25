"""Tests for local files."""

from hashlib import sha256
from pathlib import Path

from watershipup.local_files import make_checksum


def test_make_checksum(tmp_path: Path) -> None:
    """`make_checksum` must return the file's SHA-256 in uppercase."""
    path = tmp_path / "index.html"
    path.write_bytes(b"made-up content")

    checksum = make_checksum(path)
    expect = sha256(b"made-up content").hexdigest().upper()

    assert checksum == expect
