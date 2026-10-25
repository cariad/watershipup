"""Fixtures for the integration tests."""

from collections.abc import Iterator

from pytest import fixture

from watershipup.storage_client import StorageClient

from .storage_zone import environment_variable


@fixture
def client() -> Iterator[StorageClient]:
    """Make a client for the test storage zone, and close it after the test.

    Yields:
        A client for the test storage zone.
    """
    with StorageClient(
        password=environment_variable("WATERSHIPUP_TEST_PASSWORD"),
        zone=environment_variable("WATERSHIPUP_TEST_ZONE"),
    ) as client:
        yield client
