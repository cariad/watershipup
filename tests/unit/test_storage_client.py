"""Unit tests for `StorageClient`."""

from pytest import mark, raises

from watershipup.storage_client import StorageClient


@mark.parametrize(
    "remote_path",
    [
        "",
        "css/",
    ],
)
def test_delete_refuses_directory(remote_path: str) -> None:
    """`delete` must refuse a path that would delete a whole directory."""
    with (
        StorageClient(
            password="made-up",
            zone="example-zone",
        ) as client,
        raises(ValueError, match="Won't delete a directory"),
    ):
        client.delete(remote_path)


@mark.parametrize(
    "directory",
    [
        "css",
        "css//",
        "../",
    ],
)
def test_list_directory_refuses_invalid_directory(directory: str) -> None:
    """`list_directory` must refuse a path that isn't a directory's."""
    with (
        StorageClient(
            password="made-up",
            zone="example-zone",
        ) as client,
        raises(ValueError, match="Not a directory's path"),
    ):
        client.list_directory(directory)
