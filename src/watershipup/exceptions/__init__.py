"""watershipup's own exceptions, each a `WatershipupError`."""

from .request_failed_error import RequestFailedError
from .watershipup_error import WatershipupError

__all__ = [
    "RequestFailedError",
    "WatershipupError",
]
