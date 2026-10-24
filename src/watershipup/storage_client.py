"""The `StorageClient` class, which interacts with a storage zone's HTTP API."""

from pathlib import Path
from urllib.parse import quote

import httpx2

from .exceptions import RequestFailedError

STORAGE_HOST = "storage.bunnycdn.com"


class StorageClient:
    """A client for a storage zone's HTTP API."""

    def __init__(
        self,
        *,
        password: str,
        zone: str,
    ) -> None:
        """Make a client for a storage zone.

        Args:
            password: The storage zone's password.
            zone: The storage zone's name.
        """
        self._headers = {
            "AccessKey": password,
        }

        self._timeout = httpx2.Timeout(
            120,
            connect=30,
        )

        self._zone = zone

    def make_url(
        self,
        remote_path: str,
    ) -> str:
        """Make the storage zone URL for a remote path.

        Args:
            remote_path: The unencoded remote path.

        Returns:
            URL.
        """
        return f"https://{STORAGE_HOST}/{self._zone}/{quote(remote_path)}"

    def upload(
        self,
        local_path: Path,
        remote_path: str,
    ) -> None:
        """Upload a file, replacing any file already at its path.

        Args:
            local_path: Path to the local file to upload.
            remote_path: Storage zone path to upload to.

        Raises:
            httpx2.RequestError: When bunny.net can't be reached, or its
                response can't be read.
            OSError: When the file can't be read.
            RequestFailedError: When bunny.net doesn't answer with HTTP 201.
        """
        url = self.make_url(remote_path)

        with local_path.open("rb") as f:
            response = httpx2.put(
                url,
                content=f,
                headers=self._headers,
                timeout=self._timeout,
            )

        if response.status_code == 201:
            return

        raise RequestFailedError(
            "PUT",
            remote_path,
            response.status_code,
            response.reason_phrase,
        )
