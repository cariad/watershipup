"""Unit tests for `StorageClient`."""

from pytest import mark

from watershipup.storage_client import StorageClient


@mark.parametrize(
    ["remote_path", "expect"],
    [
        (
            "index.html",
            "https://storage.bunnycdn.com/foo/index.html",
        ),
        (
            "test_upload/file +#%41.txt",
            "https://storage.bunnycdn.com/foo/test_upload/file%20%2B%23%2541.txt",
        ),
    ],
)
def test_make_url(
    remote_path: str,
    expect: str,
) -> None:
    """`make_url` must create a properly encoded URL."""
    client = StorageClient(
        password="",
        zone="foo",
    )

    url = client.make_url(remote_path)
    assert url == expect
