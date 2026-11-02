"""Integration tests for publishing."""

from pathlib import Path
from uuid import uuid4

from tests.checksum_helpers import checksum_of
from tests.file_helpers import write_files
from watershipup import PublishReport, publish
from watershipup.publishing import plan_publish
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


def test_plan_publish(
    client: StorageClient,
    tmp_path: Path,
) -> None:
    """`plan_publish` must plan a publish without uploading or deleting anything."""
    write_files(
        tmp_path,
        {
            "test_plan_publish/css/old.css": uuid4().bytes,
            "test_plan_publish/feed.xml": uuid4().bytes,
            "test_plan_publish/index.html": uuid4().bytes,
            "test_plan_publish/old.html": uuid4().bytes,
        },
    )

    _publish(tmp_path)

    # Different on every run, so the page is always uploaded.
    (tmp_path / "test_plan_publish/index.html").write_bytes(uuid4().bytes)
    (tmp_path / "test_plan_publish/css/old.css").unlink()
    (tmp_path / "test_plan_publish/old.html").unlink()

    # A page, so if `plan_publish` ever uploaded it, the next run's first publish would
    # delete it.
    write_files(
        tmp_path,
        {
            "test_plan_publish/new.html": uuid4().bytes,
        },
    )

    before = {
        zone_file
        for zone_file in client.walk_zone()
        if zone_file.path.startswith("test_plan_publish/")
    }

    plan = plan_publish(
        tmp_path,
        client,
    )

    after = {
        zone_file
        for zone_file in client.walk_zone()
        if zone_file.path.startswith("test_plan_publish/")
    }

    # The first publish deleted every other page and feed in the zone, so the only
    # deletion is this test's.
    result = (
        tuple(local_file.remote_path for local_file in plan.uploads),
        plan.deletions,
        plan.unchanged,
    )

    expect = (
        ("test_plan_publish/index.html", "test_plan_publish/new.html"),
        ("test_plan_publish/old.html",),
        ("test_plan_publish/feed.xml",),
    )

    assert result == expect

    # The zone keeps any asset left by other tests, so only this one is looked for.
    assert "test_plan_publish/css/old.css" in plan.kept

    # Each `ZoneFile` holds its checksum, so this shows that nothing was uploaded or
    # deleted.
    assert after == before


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
