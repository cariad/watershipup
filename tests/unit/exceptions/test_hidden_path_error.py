"""Tests for `HiddenPathError`."""

from pathlib import Path

from pytest import raises

from watershipup.exceptions import HiddenPathError, WatershipupError


def test_hidden_path_error_is_watershipup_error() -> None:
    """A `HiddenPathError` must be caught as a `WatershipupError`."""
    with raises(WatershipupError):
        raise HiddenPathError(Path(".env"))


def test_hidden_path_error_str() -> None:
    """A `HiddenPathError` must name the hidden file or directory."""
    error = HiddenPathError(Path("css/.DS_Store"))

    message = str(error)
    expect = "Won't publish a hidden file or directory: 'css/.DS_Store'"

    assert message == expect
