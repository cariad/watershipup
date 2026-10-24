"""Fixtures for the integration tests."""

from pytest import fixture

from watershipup.storage_client import StorageClient

from .storage_zone import environment_variable


@fixture
def client() -> StorageClient:
    """Make a client for the test storage zone.

    Returns:
        A client for the test storage zone.
    """
    return StorageClient(
        password=environment_variable("WATERSHIPUP_TEST_PASSWORD"),
        zone=environment_variable("WATERSHIPUP_TEST_ZONE"),
    )
