"""Functions for deciding which failed requests to send again."""

from ssl import SSLCertVerificationError

import httpx2

BUSY_MESSAGE = b"Unable to process request"
"""What bunny.net's 400 says when a zone is over its listing or delete limits."""

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
