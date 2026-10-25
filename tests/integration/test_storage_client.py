"""Integration tests for `StorageClient`."""

from pathlib import Path
from uuid import uuid4

from pytest import mark, raises

from tests.checksum_helpers import checksum_of
from watershipup.exceptions import RequestFailedError
from watershipup.storage_client import StorageClient
from watershipup.zone_file import ZoneFile
from watershipup.zone_listing import ZoneListing

from .storage_zone import is_stored, read_storage


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

    checksum = checksum_of(local_path.read_bytes())

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


def test_delete_wrong_password(
    wrong_password_client: StorageClient,
) -> None:
    """`delete` must raise `RequestFailedError` when the zone refuses the password."""
    with raises(RequestFailedError) as ex:
        wrong_password_client.delete("test_delete_wrong_password.txt")

    assert ex.value.method == "DELETE"
    assert ex.value.path == "test_delete_wrong_password.txt"
    assert ex.value.status == 401


def test_list(
    client: StorageClient,
    tmp_path: Path,
) -> None:
    """`list_directory` must find a directory's files and subdirectories."""
    # Different on every run, so a file left by an earlier run can't pass.
    contents = {
        "test_list_directory/a.txt": uuid4().bytes,
        "test_list_directory/b.txt": uuid4().bytes,
        "test_list_directory/sub/c.txt": uuid4().bytes,
    }

    for remote_path, content in contents.items():
        local_path = tmp_path / "file.txt"
        local_path.write_bytes(content)

        client.upload(
            local_path,
            remote_path,
            checksum=checksum_of(content),
        )

    listing = client.list_directory("test_list_directory/")

    # Only the paths this test uploads, so an entry left by an earlier version of the
    # test can't fail it.
    #
    # bunny.net's order isn't relied on.
    found = (
        {file for file in listing.files if file.path in contents},
        set(listing.directories) & {"test_list_directory/sub/"},
    )

    expect = (
        {
            ZoneFile(
                "test_list_directory/a.txt",
                checksum_of(contents["test_list_directory/a.txt"]),
                "",
            ),
            ZoneFile(
                "test_list_directory/b.txt",
                checksum_of(contents["test_list_directory/b.txt"]),
                "",
            ),
        },
        {
            "test_list_directory/sub/",
        },
    )

    assert found == expect


def test_list_directory_missing(
    client: StorageClient,
) -> None:
    """`list_directory` must find nothing in a directory that doesn't exist."""
    listing = client.list_directory("test_list_directory_missing/")
    expect = ZoneListing(
        (),
        (),
    )

    assert listing == expect


def test_list_directory_root(
    client: StorageClient,
    tmp_path: Path,
) -> None:
    """`list_directory` must find a file in the zone's root."""
    # Different on every run, so a file left by an earlier run can't pass.
    content = uuid4().bytes
    checksum = checksum_of(content)

    local_path = tmp_path / "file.txt"
    local_path.write_bytes(content)

    client.upload(
        local_path,
        "test_list_root.txt",
        checksum=checksum,
    )

    listing = client.list_directory("")

    expect = ZoneFile(
        "test_list_root.txt",
        checksum,
        "",
    )

    assert expect in listing.files


def test_list_directory_wrong_password(
    wrong_password_client: StorageClient,
) -> None:
    """`list_directory` must raise `RequestFailedError` when the password's wrong."""
    with raises(RequestFailedError) as ex:
        wrong_password_client.list_directory("test_list_directory_wrong_password/")

    assert ex.value.method == "GET"
    assert ex.value.path == "test_list_directory_wrong_password/"
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
    checksum = checksum_of(content)

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
        checksum = checksum_of(content)

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

    checksum = checksum_of(b"Something else")

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
    wrong_password_client: StorageClient,
) -> None:
    """`upload` must raise `RequestFailedError` when the zone refuses the password."""
    local_path = tmp_path / "file.txt"
    local_path.write_text("Hello, world!")

    checksum = checksum_of(local_path.read_bytes())

    with raises(RequestFailedError) as ex:
        wrong_password_client.upload(
            local_path,
            "test_upload_wrong_password.txt",
            checksum=checksum,
        )

    assert ex.value.method == "PUT"
    assert ex.value.path == "test_upload_wrong_password.txt"
    assert ex.value.status == 401
