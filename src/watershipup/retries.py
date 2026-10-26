"""Functions for deciding which failed requests to send again."""

from ssl import SSLCertVerificationError

import httpx2

BUSY_MESSAGE = b"Unable to process request"
"""What bunny.net's 400 says when a zone is over its listing or delete limits."""

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
