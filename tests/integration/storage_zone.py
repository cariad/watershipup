"""Functions for the test storage zone.

They read the zone's password from `WATERSHIPUP_TEST_PASSWORD` themselves, so
the password itself is never a test's argument or a fixture's value, which
pytest could print.
"""

import os

import httpx2
from pytest import fail

from watershipup.urls import make_zone_url


def _get(
    path: str,
) -> httpx2.Response:
    """Send a `GET` for a path in the test zone.

    Args:
        path: The path in the zone.

    Returns:
        The response.
    """
    password = environment_variable("WATERSHIPUP_TEST_PASSWORD")
    zone = environment_variable("WATERSHIPUP_TEST_ZONE")
    url = make_zone_url(zone, path)

    return httpx2.get(
        url,
        headers={
            "AccessKey": password,
        },
    )


def environment_variable(name: str) -> str:
    """Read an environment variable, or fail the test if it isn't set.

    `os.environ[name]` would raise a `KeyError` instead, and pytest would print
    the start of the whole environment with it.

    Args:
        name: The environment variable's name.

    Returns:
        The environment variable's value.
    """
    if value := os.environ.get(name):
        return value

    fail(
        f"{name} must be set",
        pytrace=False,
    )


def is_stored(
    path: str,
) -> bool:
    """Check whether or not a file exists in the test zone.

    Args:
        path: The file's path in the zone.

    Returns:
        `True` if the file exists in the zone.
    """
    response = _get(path)

    if response.status_code not in (200, 404):
        fail(f"GET {path!r} answered {response.status_code} {response.reason_phrase}")

    return response.status_code == 200


def read_storage(
    path: str,
) -> bytes:
    """Download a file from the test zone.

    Args:
        path: The file's path in the zone.

    Returns:
        The file's bytes.
    """
    response = _get(path)

    if response.status_code != 200:
        fail(f"GET {path!r} answered {response.status_code} {response.reason_phrase}")

    return response.content
