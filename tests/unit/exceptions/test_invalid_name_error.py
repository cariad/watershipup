"""Tests for `InvalidNameError`."""

from pathlib import Path

from pytest import raises

from watershipup.exceptions import InvalidNameError, WatershipupError


def test_invalid_name_error_is_watershipup_error() -> None:
    """An `InvalidNameError` must be caught as a `WatershipupError`."""
    with raises(WatershipupError):
        raise InvalidNameError(Path(" index.html"))


def test_invalid_name_error_str() -> None:
    """An `InvalidNameError` must name the file, with control characters escaped."""
    error = InvalidNameError(Path("css/tab\there.css"))

    message = str(error)
    expect = (
        "Won't publish a file whose path has a name that bunny.net would "
        "reject: 'css/tab\\there.css'"
    )

    assert message == expect
