"""Integration tests for `StorageClient`."""

from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from pytest import mark, raises

from watershipup.exceptions import RequestFailedError
from watershipup.storage_client import StorageClient

from .storage_zone import environment_variable, is_stored, read_storage


@mark.parametrize(
    "remote_path",
    [
        "test_delete.txt",
        "test_delete/file +#%41.txt",
    ],
)
def test_delete(
    client: StorageClient,
    remote_path: str,
    tmp_path: Path,
) -> None:
    """`delete` must remove the file from the zone."""
    local_path = tmp_path / "file.txt"
    local_path.write_text("Hello, world!")

    checksum = sha256(local_path.read_bytes()).hexdigest().upper()

    client.upload(
        local_path,
        remote_path,
        checksum=checksum,
    )

    stored_before = is_stored(remote_path)
    client.delete(remote_path)
    stored_after = is_stored(remote_path)

    assert stored_before
    assert not stored_after


def test_delete_missing(
    client: StorageClient,
) -> None:
    """`delete` must succeed when the file is already gone."""
    # The first delete makes sure the file is gone, whatever the zone held.
    client.delete("test_delete_missing.txt")
    client.delete("test_delete_missing.txt")


def test_delete_wrong_password() -> None:
    """`delete` must raise `RequestFailedError` when the zone refuses the password."""
    with (
        StorageClient(
            password="not-the-password",
            zone=environment_variable("WATERSHIPUP_TEST_ZONE"),
        ) as client,
        raises(RequestFailedError) as ex,
    ):
        client.delete("test_delete_wrong_password.txt")

    assert ex.value.method == "DELETE"
    assert ex.value.path == "test_delete_wrong_password.txt"
    assert ex.value.status == 401


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
        remote_path,
    )

    assert found_bytes == content


def test_upload_two_files(
    client: StorageClient,
    tmp_path: Path,
) -> None:
    """`upload` must store a second file through the client that stored the first."""
    # Different on every run, so a file left by an earlier run can't pass.
    expect = {
        "test_upload_two_files/1.txt": uuid4().bytes,
        "test_upload_two_files/2.txt": uuid4().bytes,
    }

    # One client for both, so the second upload can reuse the first's connection.
    for remote_path, content in expect.items():
        checksum = sha256(content).hexdigest().upper()

        local_path = tmp_path / "file.txt"
        local_path.write_bytes(content)

        client.upload(
            local_path,
            remote_path,
            checksum=checksum,
        )

    found = {remote_path: read_storage(remote_path) for remote_path in expect}

    assert found == expect


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
    local_path = tmp_path / "file.txt"
    local_path.write_text("Hello, world!")

    checksum = sha256(local_path.read_bytes()).hexdigest().upper()

    with (
        StorageClient(
            password="not-the-password",
            zone=environment_variable("WATERSHIPUP_TEST_ZONE"),
        ) as client,
        raises(RequestFailedError) as ex,
    ):
        client.upload(
            local_path,
            "test_upload_wrong_password.txt",
            checksum=checksum,
        )

    assert ex.value.method == "PUT"
    assert ex.value.path == "test_upload_wrong_password.txt"
    assert ex.value.status == 401
