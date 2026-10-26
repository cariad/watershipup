"""Functions for deciding which failed requests to send again, and sending them."""

import logging
import time
from collections.abc import Callable
from ssl import SSLCertVerificationError

import httpx2

_logger = logging.getLogger(__name__)

BUSY_MESSAGE = b"Unable to process request"
"""What bunny.net's 400 says when a zone is over its listing or delete limits."""

MAX_ATTEMPTS = 5
"""The most times that a request is sent, counting the first."""

MAX_BACKOFF_SECONDS = 10
"""The longest that watershipup's own wait between retries grows to, as it doubles."""

MAX_REQUESTED_WAIT_SECONDS = 60
"""The longest wait that watershipup honours from a response's `Retry-After`."""

PERMANENT_ERRORS = (
    httpx2.LocalProtocolError,
    httpx2.ProxyError,
    httpx2.UnsupportedProtocol,
)
"""The connection errors that a retry can't fix."""

PERMANENT_STATUSES = frozenset(
    {
        501,
        505,
    }
)
"""The 5xx statuses that say the server doesn't support the request."""

RETRYABLE_STATUSES = frozenset(
    {
        408,
        429,
    }
)
"""The statuses below 500 that are always worth retrying."""


def is_retryable_error(ex: Exception) -> bool:
    """Check whether a request that raised an error is worth sending again.

    Args:
        ex: The error that the request raised.

    Returns:
        `True` for a connection error, like failing to connect, a timeout or a dropped
        connection, but not for a fault in the request itself, a proxy's refusal or a
        certificate that can't be verified.
    """
    if not isinstance(ex, httpx2.TransportError) or isinstance(ex, PERMANENT_ERRORS):
        return False

    # httpx2 raises a failed certificate check as a `ConnectError` caused by
    # httpcore2's `ConnectError`. httpcore2 re-raises its own with `from None`, so the
    # `SSLCertVerificationError` is only that error's context.
    cause = ex.__cause__ or ex.__context__

    while cause is not None:
        if isinstance(cause, SSLCertVerificationError):
            return False

        cause = cause.__cause__ or cause.__context__

    return True


def is_retryable_status(status: int, body: bytes) -> bool:
    """Check whether a request that bunny.net refused is worth sending again.

    Args:
        status: The response's status code.
        body: The response's body.

    Returns:
        `True` for 408, 429 and every 5xx except 501 and 505, and for a 400 that says
        the zone is over its listing or delete limits.
    """
    if status in RETRYABLE_STATUSES:
        return True

    if 500 <= status <= 599:
        return status not in PERMANENT_STATUSES

    return status == 400 and BUSY_MESSAGE in body


def retry_delay(
    retry_index: int,
    retry_after: str | None,
) -> int:
    """Calculate how long to wait before retrying a request.

    watershipup's own backoff doubles with each retry, from 1 second up to
    `MAX_BACKOFF_SECONDS`.

    bunny.net can ask for a longer wait with a `Retry-After` header in seconds, which
    is honoured up to `MAX_REQUESTED_WAIT_SECONDS`. A shorter one, or one in any other
    form, like a date, leaves the backoff as it is.

    Args:
        retry_index: 1 for the first retry, 2 for the second, and so on.
        retry_after: The response's `Retry-After` header, if it had one.

    Returns:
        The number of seconds to wait.

    Raises:
        ValueError: When `retry_index` is less than 1.
    """
    if retry_index < 1:
        raise ValueError(f"Retry index must be at least 1: {retry_index!r}")

    # Capping the exponent as well keeps a huge index from making a huge number.
    backoff: int = min(
        2 ** min(retry_index - 1, MAX_BACKOFF_SECONDS),
        MAX_BACKOFF_SECONDS,
    )

    if retry_after is None:
        return backoff

    if not (retry_after.isascii() and retry_after.isdigit()):
        return backoff

    try:
        requested = int(retry_after)
    except ValueError:
        # By default, `int()` refuses more than 4,300 digits, far beyond the cap.
        requested = MAX_REQUESTED_WAIT_SECONDS

    return min(
        max(backoff, requested),
        MAX_REQUESTED_WAIT_SECONDS,
    )


def send_with_retries(
    send: Callable[[], httpx2.Response],
    sleep: Callable[[float], object] = time.sleep,
) -> httpx2.Response:
    """Send a request, and send it again while it fails in a way that might not last.

    The request is sent up to `MAX_ATTEMPTS` times, waiting as long as `retry_delay`
    says before each retry, and logging a warning that says why.

    Args:
        send: Sends the request once, and returns bunny.net's response.
        sleep: Waits for a number of seconds.

    Returns:
        The first response that isn't worth sending again, such as a success, or else
        the last one, for the caller to check.

    Raises:
        Exception: Any other error that `send` raises, at once, without a retry.
        httpx2.TransportError: When a connection error can't be retried, or the last
            attempt fails with one.
    """
    for retry_index in range(1, MAX_ATTEMPTS):
        try:
            response = send()
        except httpx2.TransportError as ex:
            if not is_retryable_error(ex):
                raise

            delay = retry_delay(retry_index, None)

            _logger.warning(
                "Sending again in %d s, after an error: %s",
                delay,
                ex,
            )

            sleep(delay)
            continue

        if not is_retryable_status(response.status_code, response.content):
            return response

        delay = retry_delay(
            retry_index,
            response.headers.get("Retry-After"),
        )

        _logger.warning(
            "Sending again in %d s, after %d %s",
            delay,
            response.status_code,
            response.reason_phrase,
        )

        sleep(delay)

    # The last attempt's response or error goes to the caller.
    return send()
