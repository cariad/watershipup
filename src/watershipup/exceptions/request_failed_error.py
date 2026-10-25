"""The `RequestFailedError` class, raised when a storage zone refuses a request."""

from .watershipup_error import WatershipupError


class RequestFailedError(WatershipupError):
    """Raised when a storage zone answers a request with an unexpected status.

    Attributes:
        method: The request's method, such as "PUT".
        path: The path in the storage zone, such as "css/site.css", or "" for its root.
        status: The response's status code, such as 401.
        reason: The response's reason phrase, such as "Unauthorized".
    """

    def __init__(
        self,
        method: str,
        path: str,
        status: int,
        reason: str,
    ) -> None:
        """Describe a failed request.

        Args:
            method: The request's method, such as "PUT".
            path: The path in the storage zone, or "" for its root.
            status: The response's status code, such as 401.
            reason: The response's reason phrase, such as "Unauthorized".
        """
        super().__init__(method, path, status, reason)
        self.method = method
        self.path = path
        self.status = status
        self.reason = reason

    def __str__(self) -> str:
        """Describe the failed request on one line."""
        # The zone's root has the path "", which would read as ''.
        path = repr(self.path) if self.path else "the zone's root"
        return f"{self.method} {path} failed with {self.status} {self.reason}"
