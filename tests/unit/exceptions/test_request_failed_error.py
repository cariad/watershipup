"""Tests for `RequestFailedError`."""

from pytest import raises

from watershipup.exceptions import RequestFailedError, WatershipupError


def test_request_failed_error_is_watershipup_error() -> None:
    """A `RequestFailedError` must be caught as a `WatershipupError`."""
    with raises(WatershipupError):
        raise RequestFailedError(
            "PUT",
            "css/site.css",
            401,
            "Unauthorized",
        )


def test_request_failed_error_str() -> None:
    """A `RequestFailedError` must describe the request and its response."""
    error = RequestFailedError(
        "PUT",
        "css/site.css",
        401,
        "Unauthorized",
    )

    expect = "PUT 'css/site.css' failed with 401 Unauthorized"

    assert str(error) == expect
