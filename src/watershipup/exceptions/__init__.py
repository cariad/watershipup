"""watershipup's own exceptions, each a `WatershipupError`."""

from .hidden_path_error import HiddenPathError
from .no_files_error import NoFilesError
from .request_failed_error import RequestFailedError
from .watershipup_error import WatershipupError

__all__ = [
    "HiddenPathError",
    "NoFilesError",
    "RequestFailedError",
    "WatershipupError",
]
