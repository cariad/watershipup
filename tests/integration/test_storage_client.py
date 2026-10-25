"""Integration tests for `StorageClient`."""

from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from pytest import mark, raises

from watershipup.exceptions import RequestFailedError
from watershipup.storage_client import StorageClient

from .storage_zone import environment_variable, read_storage


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
    checksum = sha256(content).hexdigest().upper()

    local_path = tmp_path / "file.txt"
    local_path.write_bytes(content)

    client.upload(
        local_path,
        remote_path,
        checksum=checksum,
    )

    found_bytes = read_storage(
        client,
        remote_path,
    )

    assert found_bytes == content


def test_upload_wrong_checksum(
    client: StorageClient,
    tmp_path: Path,
) -> None:
    """`upload` must raise `RequestFailedError` when the checksum is wrong."""
    local_path = tmp_path / "file.txt"
    local_path.write_text("Hello, world!")

    checksum = sha256(b"Something else").hexdigest().upper()

    with raises(RequestFailedError) as ex:
        client.upload(
            local_path,
            "test_upload_wrong_checksum.txt",
            checksum=checksum,
        )

    assert ex.value.method == "PUT"
    assert ex.value.path == "test_upload_wrong_checksum.txt"
    assert ex.value.status == 400


def test_upload_wrong_password(
    tmp_path: Path,
) -> None:
    """`upload` must raise `RequestFailedError` when the zone refuses the password."""
    client = StorageClient(
        password="not-the-password",
        zone=environment_variable("WATERSHIPUP_TEST_ZONE"),
    )

    local_path = tmp_path / "file.txt"
    local_path.write_text("Hello, world!")

    checksum = sha256(local_path.read_bytes()).hexdigest().upper()

    with raises(RequestFailedError) as ex:
        client.upload(
            local_path,
            "test_upload_wrong_password.txt",
            checksum=checksum,
        )

    assert ex.value.method == "PUT"
    assert ex.value.path == "test_upload_wrong_password.txt"
    assert ex.value.status == 401
