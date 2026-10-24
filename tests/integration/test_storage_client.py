"""Integration tests for `StorageClient`."""

from pathlib import Path
from uuid import uuid4

from pytest import mark

from watershipup.storage_client import StorageClient

from .storage_zone import read_storage


@mark.parametrize(
    "remote_path",
    [
        "test_upload.txt",
        "test_upload/file +#%41.txt",
    ],
)
def test_upload(
    client: StorageClient,
    remote_path: str,
    tmp_path: Path,
) -> None:
    """`upload` must store the file's bytes at its path in the zone."""
    # Different on every run, so a file left by an earlier run can't pass.
    content = uuid4().bytes

    local_path = tmp_path / "file.txt"
    local_path.write_bytes(content)

    client.upload(
        local_path,
        remote_path,
    )

    found_bytes = read_storage(
        client,
        remote_path,
    )

    assert found_bytes == content
