"""The `StorageClient` class, which interacts with a storage zone's HTTP API."""

from http.cookiejar import CookieJar, DefaultCookiePolicy
from pathlib import Path
from types import TracebackType
from typing import Self

import httpx2

from .exceptions import RequestFailedError
from .urls import make_zone_url


class StorageClient:
    """A client for a storage zone's HTTP API.

    Connections are kept open between requests, so close it when you're done, or use it
    as a context manager.
    """

    def __enter__(self) -> Self:
        """Use the client as a context manager.

        Returns:
            The client.

        Raises:
            RuntimeError: When the client has already been used or closed.
        """
        self._client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the client's connections."""
        self.close()

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
        # Reject every cookie, so requests carry nothing from earlier responses.
        cookies = CookieJar(
            DefaultCookiePolicy(
                allowed_domains=[],
            ),
        )

        headers = {
            "AccessKey": password,
        }

        timeout = httpx2.Timeout(
            120,
            connect=30,
        )

        self._client = httpx2.Client(
            cookies=cookies,
            headers=headers,
            timeout=timeout,
        )

        self._zone = zone

    def close(self) -> None:
        """Close the client's connections."""
        self._client.close()

    def upload(
        self,
        local_path: Path,
        remote_path: str,
        *,
        checksum: str,
    ) -> None:
        """Upload a file, replacing any file already at its path.

        Args:
            local_path: Path to the local file to upload.
            remote_path: Storage zone path to upload to.
            checksum: The file's SHA-256, in uppercase hexadecimal.

        Raises:
            httpx2.RequestError: When bunny.net can't be reached, or its
                response can't be read.
            OSError: When the file can't be read.
            RequestFailedError: When bunny.net doesn't answer with HTTP 201,
                such as when the file doesn't match its checksum.
            RuntimeError: When the client has been closed.
        """
        headers = {
            "Checksum": checksum,
        }

        url = make_zone_url(
            self._zone,
            remote_path,
        )

        with local_path.open("rb") as f:
            response = self._client.put(
                url,
                content=f,
                headers=headers,
            )

        if response.status_code == 201:
            return

        raise RequestFailedError(
            "PUT",
            remote_path,
            response.status_code,
            response.reason_phrase,
        )
