"""Tests for deciding which failed requests to send again."""

from ssl import SSLCertVerificationError, SSLEOFError

import httpx2
from pytest import mark, param, raises

from watershipup.retries import is_retryable_error, is_retryable_status, retry_delay

BUSY_BODY = b'{"HttpCode":400,"Message":"Unable to process request"}'
"""A made-up 400 body for a zone that's over its listing or delete limits."""

CHECKSUM_BODY = (
    b'{"HttpCode":400,"Message":"Unable to upload file: Exception when writing file: '
    b'Checksum missmatch, skipping commit"}'
)
"""The 400 body that bunny.net sends for a checksum mismatch, in its own spelling.

The typo isn't documented, but we discovered it during our own testing.
"""


def _make_connect_error(cause: Exception) -> httpx2.ConnectError:
    """Make a `ConnectError` chained to an original error, as httpx2 raises one.

    httpx2 raises its own error from httpcore2's. httpcore2 re-raises its own with
    `from None`, so the original error is only that error's context.

    Args:
        cause: The original error.

    Returns:
        The `ConnectError`.
    """
    middle = Exception("made-up")
    middle.__context__ = cause

    error = httpx2.ConnectError("made-up")
    error.__cause__ = middle

    return error


@mark.parametrize(
    "error",
    [
        httpx2.ConnectError("made-up"),
        httpx2.ReadTimeout("made-up"),
        httpx2.RemoteProtocolError("made-up"),
        httpx2.PoolTimeout("made-up"),
        _make_connect_error(ConnectionRefusedError("made-up")),
        _make_connect_error(SSLEOFError("made-up")),
    ],
)
def test_is_retryable_error(error: Exception) -> None:
    """`is_retryable_error` must be true for a connection error."""
    retryable = is_retryable_error(error)
    assert retryable


@mark.parametrize(
    "error",
    [
        httpx2.LocalProtocolError("made-up"),
        httpx2.ProxyError("made-up"),
        httpx2.UnsupportedProtocol("made-up"),
        httpx2.DecodingError("made-up"),
        httpx2.TooManyRedirects("made-up"),
        _make_connect_error(SSLCertVerificationError("made-up")),
        OSError("made-up"),
        ValueError("made-up"),
    ],
)
def test_is_retryable_error_when_not(error: Exception) -> None:
    """`is_retryable_error` must be false for a fault that a retry can't fix."""
    retryable = is_retryable_error(error)
    assert not retryable


@mark.parametrize(
    ["status", "body"],
    [
        (408, b""),
        (429, b""),
        (500, b""),
        (503, b""),
        (599, b""),
        (400, BUSY_BODY),
    ],
)
def test_is_retryable_status(status: int, body: bytes) -> None:
    """`is_retryable_status` must be true for a refusal that may pass later."""
    retryable = is_retryable_status(status, body)
    assert retryable


@mark.parametrize(
    ["status", "body"],
    [
        (400, CHECKSUM_BODY),
        (400, b""),
        (401, b""),
        (403, b""),
        (404, b""),
        (404, BUSY_BODY),
        (409, b""),
        (499, b""),
        (501, b""),
        (505, b""),
        (600, b""),
    ],
)
def test_is_retryable_status_when_not(status: int, body: bytes) -> None:
    """`is_retryable_status` must be false for a refusal that will happen again."""
    retryable = is_retryable_status(status, body)
    assert not retryable


@mark.parametrize(
    ["retry", "expect"],
    [
        (1, 1),
        (2, 2),
        (3, 4),
        (4, 8),
        (5, 10),
        (6, 10),
    ],
)
def test_retry_delay(retry: int, expect: int) -> None:
    """`retry_delay` must double the wait with each retry, up to 10 seconds."""
    delay = retry_delay(retry, None)
    assert delay == expect


@mark.parametrize(
    "retry_after",
    [
        "Fri, 01 Jan 2100 00:00:00 GMT",
        "soon",
        "5.5",
        "",
        "+30",
        "1_0",
        "\uff13\uff10",  # "30" in fullwidth digits.
        "\u0663\u0660",  # "30" in Arabic-Indic digits.
    ],
)
def test_retry_delay_ignores_other_retry_after(retry_after: str) -> None:
    """`retry_delay` must ignore a `Retry-After` that isn't a number of seconds.

    Each one that could be read as a wait asks for longer than the second retry's
    backoff of 2 seconds, so honouring it would change the delay.
    """
    delay = retry_delay(2, retry_after)
    expect = 2

    assert delay == expect


@mark.parametrize("retry", [0, -1])
def test_retry_delay_refuses_index(retry: int) -> None:
    """`retry_delay` must refuse a retry index below 1."""
    with raises(ValueError, match="at least 1"):
        retry_delay(retry, None)


@mark.parametrize(
    ["retry", "retry_after", "expect"],
    [
        (1, "3", 3),
        (1, "30", 30),
        (1, "120", 60),
        (1, "0", 1),
        (3, "2", 4),
        param(1, "9" * 5000, 60, id="1-5000-digits-60"),
    ],
)
def test_retry_delay_with_retry_after(
    retry: int,
    retry_after: str,
    expect: int,
) -> None:
    """`retry_delay` must honour `Retry-After`, up to 60 seconds, but not wait less."""
    delay = retry_delay(retry, retry_after)
    assert delay == expect
