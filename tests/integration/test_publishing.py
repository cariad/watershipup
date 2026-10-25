"""Integration tests for publishing."""

from pathlib import Path
from uuid import uuid4

from tests.checksum_helpers import checksum_of
from tests.file_helpers import write_files
from watershipup import PublishReport, publish
from watershipup.storage_client import StorageClient
from watershipup.zone_file import ZoneFile

from .storage_zone import environment_variable, is_stored


def _publish(directory: Path) -> PublishReport:
    """Publish a directory to the test zone.

    Args:
        directory: The directory to publish.

    Returns:
        What the publish did.
    """
    return publish(
        directory,
        password=environment_variable("WATERSHIPUP_TEST_PASSWORD"),
        zone=environment_variable("WATERSHIPUP_TEST_ZONE"),
    )


def test_publish(
    client: StorageClient,
    tmp_path: Path,
) -> None:
    """`publish` must upload every file in the directory to the zone."""
    # Different on every run, so files left by an earlier run can't pass.
    contents = {
        "test_publish/css/site.css": uuid4().bytes,
        "test_publish/feed.xml": uuid4().bytes,
        "test_publish/index.html": uuid4().bytes,
    }

    write_files(
        tmp_path,
        contents,
    )

    report = _publish(tmp_path)

    # Only the paths this test uploads, because the zone keeps any asset left by an
    # earlier version of the test.
    found = {
        zone_file for zone_file in client.walk_zone() if zone_file.path in contents
    }

    expect = {
        ZoneFile(
            remote_path,
            checksum_of(content),
            None,
        )
        for remote_path, content in contents.items()
    }

    assert report.uploaded == tuple(sorted(contents))
    assert found == expect


def test_publish_deletes_old_page(tmp_path: Path) -> None:
    """`publish` must delete a page that's no longer in the directory."""
    write_files(
        tmp_path,
        {
            "test_publish_deletes_old_page/feed.xml": uuid4().bytes,
            "test_publish_deletes_old_page/index.html": uuid4().bytes,
        },
    )

    _publish(tmp_path)

    (tmp_path / "test_publish_deletes_old_page/index.html").unlink()

    report = _publish(tmp_path)
    stored = is_stored("test_publish_deletes_old_page/index.html")

    assert "test_publish_deletes_old_page/index.html" in report.deleted
    assert report.unchanged == ("test_publish_deletes_old_page/feed.xml",)
    assert report.uploaded == ()
    assert not stored


def test_publish_keeps_old_asset(tmp_path: Path) -> None:
    """`publish` must keep an asset that's no longer in the directory."""
    write_files(
        tmp_path,
        {
            "test_publish_keeps_old_asset/css/site.css": uuid4().bytes,
            "test_publish_keeps_old_asset/index.html": uuid4().bytes,
        },
    )

    _publish(tmp_path)

    (tmp_path / "test_publish_keeps_old_asset/css/site.css").unlink()

    report = _publish(tmp_path)
    stored = is_stored("test_publish_keeps_old_asset/css/site.css")

    assert "test_publish_keeps_old_asset/css/site.css" in report.kept
    assert stored
