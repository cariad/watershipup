"""Tests for deciding which failed requests to send again, and sending them."""

import logging
from collections.abc import Callable
from ssl import SSLCertVerificationError, SSLEOFError

import httpx2
from pytest import LogCaptureFixture, mark, param, raises

from watershipup.retries import (
    is_retryable_error,
    is_retryable_status,
    retry_delay,
    send_with_retries,
)

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


def _make_send(
    *outcomes: httpx2.Response | Exception,
) -> Callable[[], httpx2.Response]:
    """Make a stand-in for sending a request, which gives made-up outcomes in turn.

    Args:
        *outcomes: Each attempt's response, or the error it raises.

    Returns:
        A function that returns or raises the next outcome each time it's called.
    """
    remaining = list(outcomes)

    def send() -> httpx2.Response:
        outcome = remaining.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome

    return send


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


def test_send_with_retries_counts_every_retry() -> None:
    """`send_with_retries` must count connection errors and refusals alike."""
    send = _make_send(
        httpx2.ConnectError("made-up"),
        httpx2.Response(503),
        httpx2.Response(201),
    )

    waits: list[float] = []

    response = send_with_retries(send, waits.append)
    status_and_waits = (response.status_code, waits)
    expect = (201, [1, 2])

    assert status_and_waits == expect


def test_send_with_retries_gives_up_on_error() -> None:
    """`send_with_retries` must raise the fifth connection error in a row."""
    send = _make_send(*[httpx2.ConnectError(f"made-up {n}") for n in range(1, 6)])
    waits: list[float] = []

    with raises(httpx2.ConnectError, match="made-up 5"):
        send_with_retries(send, waits.append)

    expect = [1, 2, 4, 8]

    assert waits == expect


def test_send_with_retries_gives_up_on_status() -> None:
    """`send_with_retries` must return the fifth retryable refusal in a row."""
    send = _make_send(
        *[httpx2.Response(503, content=f"{n}".encode()) for n in range(1, 6)]
    )
    waits: list[float] = []

    response = send_with_retries(send, waits.append)
    content_and_waits = (response.content, waits)
    expect = (b"5", [1, 2, 4, 8])

    assert content_and_waits == expect


def test_send_with_retries_honours_retry_after() -> None:
    """`send_with_retries` must wait as long as a refusal's `Retry-After` asks."""
    send = _make_send(
        httpx2.Response(429, headers={"Retry-After": "5"}),
        httpx2.Response(201),
    )

    waits: list[float] = []

    response = send_with_retries(send, waits.append)
    status_and_waits = (response.status_code, waits)
    expect = (201, [5])

    assert status_and_waits == expect


def test_send_with_retries_raises_permanent_error() -> None:
    """`send_with_retries` must raise a connection error that a retry can't fix."""
    send = _make_send(httpx2.LocalProtocolError("made-up"))
    waits: list[float] = []

    with raises(httpx2.LocalProtocolError):
        send_with_retries(send, waits.append)

    expect: list[float] = []

    assert waits == expect


def test_send_with_retries_retries_error() -> None:
    """`send_with_retries` must send a request again after a connection error."""
    send = _make_send(
        httpx2.ConnectError("made-up"),
        httpx2.Response(201),
    )

    waits: list[float] = []

    response = send_with_retries(send, waits.append)
    status_and_waits = (response.status_code, waits)
    expect = (201, [1])

    assert status_and_waits == expect


def test_send_with_retries_retries_status() -> None:
    """`send_with_retries` must send a request again after a retryable refusal."""
    send = _make_send(
        httpx2.Response(503),
        httpx2.Response(201),
    )

    waits: list[float] = []

    response = send_with_retries(send, waits.append)
    status_and_waits = (response.status_code, waits)
    expect = (201, [1])

    assert status_and_waits == expect


def test_send_with_retries_returns_permanent_refusal() -> None:
    """`send_with_retries` must return a refusal that a retry can't fix, at once."""
    send = _make_send(httpx2.Response(401))
    waits: list[float] = []

    response = send_with_retries(send, waits.append)
    status_and_waits = (response.status_code, waits)
    expect: tuple[int, list[float]] = (401, [])

    assert status_and_waits == expect


def test_send_with_retries_warns(caplog: LogCaptureFixture) -> None:
    """`send_with_retries` must warn why it's about to wait, and for how long."""
    send = _make_send(
        httpx2.ConnectError("made-up"),
        httpx2.Response(503),
        httpx2.Response(201),
    )

    caplog.set_level(logging.WARNING, logger="watershipup.retries")
    warnings_before_waits: list[str] = []

    def wait(seconds: float) -> None:
        warnings_before_waits.append(caplog.messages[-1])

    send_with_retries(send, wait)
    expect = [
        "Sending again in 1 s, after an error: made-up",
        "Sending again in 2 s, after 503 Service Unavailable",
    ]

    assert warnings_before_waits == expect
