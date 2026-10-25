"""Tests for local directories."""

import os
import sys
from hashlib import sha256
from pathlib import Path

from pytest import mark, raises

from tests.file_helpers import touch_files
from watershipup.exceptions import HiddenPathError, InvalidNameError, NoFilesError
from watershipup.local_directory import walk_local_directory
from watershipup.local_file import LocalFile

EMPTY_SHA256 = sha256(b"").hexdigest().upper()
"""The SHA-256 of an empty file."""


def test_walk_local_directory(tmp_path: Path) -> None:
    """`walk_local_directory` must find every file, sorted by path."""
    touch_files(
        tmp_path,
        "index.html",
        "css/site.css",
        "css/fonts/sans.woff2",
        "css.txt",
        "a.txt",
        ".well-known/security.txt",
    )

    assert walk_local_directory(tmp_path) == (
        LocalFile(
            tmp_path / ".well-known/security.txt",
            ".well-known/security.txt",
            EMPTY_SHA256,
        ),
        LocalFile(
            tmp_path / "a.txt",
            "a.txt",
            EMPTY_SHA256,
        ),
        LocalFile(
            tmp_path / "css.txt",
            "css.txt",
            EMPTY_SHA256,
        ),
        LocalFile(
            tmp_path / "css/fonts/sans.woff2",
            "css/fonts/sans.woff2",
            EMPTY_SHA256,
        ),
        LocalFile(
            tmp_path / "css/site.css",
            "css/site.css",
            EMPTY_SHA256,
        ),
        LocalFile(
            tmp_path / "index.html",
            "index.html",
            EMPTY_SHA256,
        ),
    )


def test_walk_local_directory_hashes_files(tmp_path: Path) -> None:
    """`walk_local_directory` must record each file's SHA-256 in uppercase."""
    (tmp_path / "a.txt").write_bytes(b"made-up a")
    (tmp_path / "b.txt").write_bytes(b"made-up b")

    local_files = walk_local_directory(tmp_path)

    expect = (
        LocalFile(
            tmp_path / "a.txt",
            "a.txt",
            sha256(b"made-up a").hexdigest().upper(),
        ),
        LocalFile(
            tmp_path / "b.txt",
            "b.txt",
            sha256(b"made-up b").hexdigest().upper(),
        ),
    )

    assert local_files == expect


@mark.parametrize(
    "subdirectories",
    [
        (),
        ("css",),
        ("css/fonts",),
        (".well-known",),
    ],
)
def test_walk_local_directory_raises_when_empty(
    subdirectories: tuple[str, ...],
    tmp_path: Path,
) -> None:
    """`walk_local_directory` must raise when there are no files to publish."""
    for subdirectory in subdirectories:
        (tmp_path / subdirectory).mkdir(parents=True)

    with raises(NoFilesError) as error:
        walk_local_directory(tmp_path)

    directory = error.value.directory
    expect = tmp_path

    assert directory == expect


def test_walk_local_directory_raises_when_file_unreadable(
    tmp_path: Path,
) -> None:
    """`walk_local_directory` must raise when a file can't be read."""
    path = tmp_path / "index.html"
    path.touch()
    path.chmod(0o000)

    try:
        with raises(PermissionError):
            walk_local_directory(tmp_path)
    finally:
        path.chmod(0o644)


def test_walk_local_directory_raises_when_hidden(tmp_path: Path) -> None:
    """`walk_local_directory` must raise with the path of a hidden file."""
    touch_files(
        tmp_path,
        "index.html",
        "css/.DS_Store",
    )

    with raises(HiddenPathError) as error:
        walk_local_directory(tmp_path)

    hidden = error.value.path
    expect = tmp_path / "css/.DS_Store"

    assert hidden == expect


def test_walk_local_directory_raises_when_hidden_without_reading(
    tmp_path: Path,
) -> None:
    """`walk_local_directory` must refuse a hidden file without reading it."""
    path = tmp_path / ".env"
    path.touch()
    path.chmod(0o000)

    try:
        with raises(HiddenPathError):
            walk_local_directory(tmp_path)
    finally:
        path.chmod(0o644)


def test_walk_local_directory_raises_when_missing(tmp_path: Path) -> None:
    """`walk_local_directory` must raise when the directory doesn't exist."""
    with raises(FileNotFoundError):
        walk_local_directory(tmp_path / "missing")


def test_walk_local_directory_raises_when_name_invalid(tmp_path: Path) -> None:
    """`walk_local_directory` must raise with the path of an invalid name."""
    touch_files(
        tmp_path,
        "index.html",
        "css/ site.css",
    )

    with raises(InvalidNameError) as error:
        walk_local_directory(tmp_path)

    invalid = error.value.path
    expect = tmp_path / "css/ site.css"

    assert invalid == expect


def test_walk_local_directory_raises_when_name_invalid_without_reading(
    tmp_path: Path,
) -> None:
    """`walk_local_directory` must refuse an invalid name without reading it."""
    path = tmp_path / " index.html"
    path.touch()
    path.chmod(0o000)

    try:
        with raises(InvalidNameError):
            walk_local_directory(tmp_path)
    finally:
        path.chmod(0o644)


@mark.skipif(
    sys.platform == "darwin",
    reason="macOS can't create a name that isn't valid UTF-8",
)
def test_walk_local_directory_raises_when_name_not_utf8(tmp_path: Path) -> None:
    """`walk_local_directory` must raise when a name isn't valid UTF-8."""
    touch_files(
        tmp_path,
        os.fsdecode(b"caf\xe9.html"),
    )

    with raises(UnicodeEncodeError):
        walk_local_directory(tmp_path)


def test_walk_local_directory_raises_when_not_a_directory(tmp_path: Path) -> None:
    """`walk_local_directory` must raise when the path isn't a directory."""
    touch_files(
        tmp_path,
        "index.html",
    )

    with raises(NotADirectoryError):
        walk_local_directory(tmp_path / "index.html")


def test_walk_local_directory_raises_when_subdirectory_unreadable(
    tmp_path: Path,
) -> None:
    """`walk_local_directory` must raise when a subdirectory can't be read."""
    subdirectory = tmp_path / "css"
    subdirectory.mkdir()
    subdirectory.chmod(0o000)

    try:
        with raises(PermissionError):
            walk_local_directory(tmp_path)
    finally:
        subdirectory.chmod(0o755)


def test_walk_local_directory_skips_broken_symlinks(tmp_path: Path) -> None:
    """`walk_local_directory` must skip broken symbolic links."""
    touch_files(
        tmp_path,
        "index.html",
    )

    (tmp_path / "old.html").symlink_to(tmp_path / "missing.html")

    assert walk_local_directory(tmp_path) == (
        LocalFile(
            tmp_path / "index.html",
            "index.html",
            EMPTY_SHA256,
        ),
    )


def test_walk_local_directory_skips_named_pipes(tmp_path: Path) -> None:
    """`walk_local_directory` must skip named pipes."""
    touch_files(
        tmp_path,
        "index.html",
    )

    os.mkfifo(tmp_path / "pipe")

    assert walk_local_directory(tmp_path) == (
        LocalFile(
            tmp_path / "index.html",
            "index.html",
            EMPTY_SHA256,
        ),
    )


def test_walk_local_directory_skips_symlinks_to_directories(
    tmp_path: Path,
) -> None:
    """`walk_local_directory` must skip symbolic links to directories."""
    touch_files(
        tmp_path,
        "target/file.txt",
        "public/index.html",
    )

    target = tmp_path / "target"
    directory = tmp_path / "public"

    (directory / "directory-symlink").symlink_to(
        target,
        target_is_directory=True,
    )

    assert walk_local_directory(directory) == (
        LocalFile(
            directory / "index.html",
            "index.html",
            EMPTY_SHA256,
        ),
    )


def test_walk_local_directory_skips_symlinks_to_files(tmp_path: Path) -> None:
    """`walk_local_directory` must skip symbolic links to files."""
    touch_files(
        tmp_path,
        "file.txt",
        "public/index.html",
    )

    target = tmp_path / "file.txt"
    directory = tmp_path / "public"

    (directory / "file-symlink.txt").symlink_to(target)

    assert walk_local_directory(directory) == (
        LocalFile(
            directory / "index.html",
            "index.html",
            EMPTY_SHA256,
        ),
    )
