"""The `StorageClient` class, which interacts with a storage zone's HTTP API."""

from collections.abc import Callable
from functools import partial
from http.cookiejar import CookieJar, DefaultCookiePolicy
from pathlib import Path
from types import TracebackType
from typing import Self

import httpx2

from .concurrency import run_all
from .content_types import content_type_of
from .exceptions import RequestFailedError
from .retries import send_with_retries
from .urls import make_zone_url
from .zone_file import ZoneFile
from .zone_listing import ZoneListing
from .zone_listings import is_valid_directory, parse_listing

MAX_LISTINGS = 5
"""The most directories to list at once, which is bunny.net's limit for listings."""


class StorageClient:
    """A client for a storage zone's HTTP API.

    Connections are kept open between requests, so close it when you're done, or use it
    as a context manager.

    A request that fails in a way that might not last, like a dropped connection or a
    503, is sent again, as `send_with_retries` describes.
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

    @staticmethod
    def _request(
        send: Callable[[], httpx2.Response],
        remote_path: str,
        *statuses: int,
    ) -> httpx2.Response:
        """Send a request, with retries, and check that bunny.net answered as expected.

        Args:
            send: Sends the request once, and returns bunny.net's response.
            remote_path: Storage zone path that the request is for.
            *statuses: The statuses that mean the request succeeded.

        Returns:
            bunny.net's response.

        Raises:
            Exception: Any error from `send_with_retries`, such as a connection error
                after the last attempt.
            RequestFailedError: When the response's status isn't one of them, after any
                retries.
        """
        response = send_with_retries(send)

        if response.status_code not in statuses:
            raise RequestFailedError(
                response.request.method,
                remote_path,
                response.status_code,
                response.reason_phrase,
            )

        return response

    def close(self) -> None:
        """Close the client's connections."""
        self._client.close()

    def delete(
        self,
        remote_path: str,
    ) -> None:
        """Delete a file from the zone.

        Deletions are idempotent, so deleting a file that doesn't exist is considered a
        successful deletion.

        The path must be to a file, never a directory. bunny.net answers 404 to a
        directory's path without its trailing slash, and deletes nothing, so that's
        considered a successful deletion too.

        Args:
            remote_path: Storage zone path of the file to delete.

        Raises:
            httpx2.RequestError: When bunny.net can't be reached, or its response can't
                be read, after any retries.
            RequestFailedError: When bunny.net doesn't answer with HTTP 200 or 404,
                after any retries.
            RuntimeError: When the client has been closed.
            ValueError: When the path is empty or invalid.
        """
        if not remote_path or remote_path.endswith("/"):
            raise ValueError(f"Won't delete a directory: {remote_path!r}")

        url = make_zone_url(
            self._zone,
            remote_path,
        )

        self._request(
            lambda: self._client.delete(url),
            remote_path,
            200,
            404,
        )

    def list_directory(
        self,
        directory: str,
    ) -> ZoneListing:
        """List one directory in the zone.

        A directory that doesn't exist lists as empty.

        Args:
            directory: "" for the zone's root, or a path ending in "/".

        Returns:
            The directory's files and subdirectories.

        Raises:
            httpx2.RequestError: When bunny.net can't be reached, or its response can't
                be read, after any retries.
            RequestFailedError: When bunny.net doesn't answer with HTTP 200, after any
                retries.
            RuntimeError: When the client has been closed.
            ValueError: When the directory or its listing is invalid.
        """
        if not is_valid_directory(directory):
            raise ValueError(f"Not a directory's path: {directory!r}")

        url = make_zone_url(
            self._zone,
            directory,
        )

        response = self._request(
            lambda: self._client.get(url),
            directory,
            200,
        )

        return parse_listing(
            directory,
            response.content,
        )

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
                response can't be read, after any retries.
            OSError: When the file can't be read.
            RequestFailedError: When bunny.net doesn't answer with HTTP 201,
                such as when the file doesn't match its checksum, after any retries.
            RuntimeError: When the client has been closed.
            ValueError: When the path has a "." or ".." segment.
        """
        headers = {
            "Checksum": checksum,
        }

        if content_type := content_type_of(remote_path):
            headers["Override-Content-Type"] = content_type

        url = make_zone_url(
            self._zone,
            remote_path,
        )

        def send() -> httpx2.Response:
            # Each attempt opens the file again, to send the whole of it.
            with local_path.open("rb") as f:
                return self._client.put(
                    url,
                    content=f,
                    headers=headers,
                )

        self._request(
            send,
            remote_path,
            201,
        )

    def walk_zone(self) -> tuple[ZoneFile, ...]:
        """Find every file in the zone.

        The zone's root is listed first, then its subdirectories, one level at a time,
        with up to `MAX_LISTINGS` listings at once.

        Returns:
            Every file in the zone, sorted by path.

        Raises:
            httpx2.RequestError: When bunny.net can't be reached, or its response can't
                be read, after any retries.
            RequestFailedError: When bunny.net doesn't answer a listing with HTTP 200,
                after any retries.
            RuntimeError: When the client has been closed.
            ValueError: When a listing is invalid.
        """

        def list_into(
            listings: dict[str, ZoneListing],
            directory: str,
        ) -> None:
            listings[directory] = self.list_directory(directory)

        files: list[ZoneFile] = []
        directories: list[str] = [""]

        while directories:
            listings: dict[str, ZoneListing] = {}

            run_all(
                [partial(list_into, listings, directory) for directory in directories],
                MAX_LISTINGS,
            )

            directories = []

            for listing in listings.values():
                files.extend(listing.files)
                directories.extend(listing.directories)

        return tuple(sorted(files, key=lambda zone_file: zone_file.path))
