"""Tests for `NoFilesError`."""

from pathlib import Path

from pytest import raises

from watershipup.exceptions import NoFilesError, WatershipupError


def test_no_files_error_is_watershipup_error() -> None:
    """A `NoFilesError` must be caught as a `WatershipupError`."""
    with raises(WatershipupError):
        raise NoFilesError(Path("public"))


def test_no_files_error_str() -> None:
    """A `NoFilesError` must name the directory with no files to publish."""
    error = NoFilesError(Path("public"))

    message = str(error)
    expect = "No files to publish in 'public'"

    assert message == expect
