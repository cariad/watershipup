"""watershipup's own exceptions, each a `WatershipupError`."""

from .hidden_path_error import HiddenPathError
from .invalid_name_error import InvalidNameError
from .no_files_error import NoFilesError
from .request_failed_error import RequestFailedError
from .watershipup_error import WatershipupError

__all__ = [
    "HiddenPathError",
    "InvalidNameError",
    "NoFilesError",
    "RequestFailedError",
    "WatershipupError",
]
